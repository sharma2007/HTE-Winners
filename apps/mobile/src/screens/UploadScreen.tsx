import React, { useState } from 'react';
import { Button, SafeAreaView, StyleSheet, Text, View } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';

import { apiBaseUrl, getToken } from '../api/client';
import { useCourse } from '../course/CourseContext';

export function UploadScreen() {
  const { courseId } = useCourse();
  const [status, setStatus] = useState<string>('');

  async function pickAndUploadPdf() {
    if (!courseId) {
      setStatus('Select a course first (Courses tab).');
      return;
    }
    const res = await DocumentPicker.getDocumentAsync({ type: ['application/pdf'] });
    if (res.canceled) return;

    const file = res.assets[0];
    setStatus('Uploading...');

    const token = await getToken();
    const form = new FormData();
    form.append('course_id', courseId);
    form.append('type', 'pdf');
    form.append(
      'file',
      {
        uri: file.uri,
        name: file.name ?? 'notes.pdf',
        type: file.mimeType ?? 'application/pdf',
      } as any
    );

    const uploadResp = await fetch(`${apiBaseUrl()}/uploads`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      body: form,
    });
    if (!uploadResp.ok) throw new Error(await uploadResp.text());
    const uploadJson = (await uploadResp.json()) as { upload_id: string };

    setStatus(`Uploaded. Enqueuing processing... (${uploadJson.upload_id})`);

    const procResp = await fetch(`${apiBaseUrl()}/uploads/${uploadJson.upload_id}/process`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    if (!procResp.ok) throw new Error(await procResp.text());

    setStatus('Processing enqueued. Open Feed to view reels once ready.');
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <Text style={styles.h1}>Upload</Text>
        <Text style={styles.meta}>Course: {courseId ?? 'None selected'}</Text>
        <View style={{ height: 16 }} />
        <Button title="Pick PDF and upload" onPress={pickAndUploadPdf} />
        <View style={{ height: 16 }} />
        <Text style={styles.status}>{status}</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#0b1220' },
  container: { flex: 1, padding: 24 },
  h1: { fontSize: 24, fontWeight: '800', color: 'white' },
  meta: { color: '#8ea0c7', marginTop: 6 },
  status: { color: '#b7c0d6', marginTop: 8, lineHeight: 18 },
});


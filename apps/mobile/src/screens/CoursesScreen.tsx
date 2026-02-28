import React, { useEffect, useState } from 'react';
import { Button, FlatList, SafeAreaView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';

import { apiFetch } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { useCourse } from '../course/CourseContext';

type Course = {
  id: string;
  title: string;
  reel_length_sec: number;
  review_frequency: string;
};

export function CoursesScreen() {
  const nav = useNavigation<any>();
  const { signOut } = useAuth();
  const { courseId, setCourseId } = useCourse();
  const [title, setTitle] = useState('');
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      const data = (await apiFetch('/courses')) as Course[];
      setCourses(data);
      if (!courseId && data.length) setCourseId(data[0].id);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function createCourse() {
    const t = title.trim();
    if (!t) return;
    await apiFetch('/courses', { method: 'POST', body: JSON.stringify({ title: t }) });
    setTitle('');
    await refresh();
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.header}>
        <Text style={styles.h1}>Your courses</Text>
        <Button title="Sign out" onPress={signOut} />
      </View>

      <View style={styles.row}>
        <TextInput
          style={styles.input}
          placeholder="New course (e.g., Calculus)"
          placeholderTextColor="#8ea0c7"
          value={title}
          onChangeText={setTitle}
        />
        <View style={{ width: 10 }} />
        <Button title="Create" onPress={createCourse} />
      </View>

      <FlatList
        data={courses}
        refreshing={loading}
        onRefresh={refresh}
        keyExtractor={(c) => c.id}
        contentContainerStyle={{ padding: 16 }}
        renderItem={({ item }) => {
          const selected = item.id === courseId;
          return (
            <View style={[styles.card, selected && styles.cardSelected]}>
              <Text style={styles.cardTitle}>{item.title}</Text>
              <Text style={styles.cardMeta}>
                Reel length: {item.reel_length_sec}s • Review: {item.review_frequency}
              </Text>
              <View style={styles.cardButtons}>
                <Button title={selected ? 'Selected' : 'Select'} onPress={() => setCourseId(item.id)} />
                <View style={{ width: 10 }} />
                <Button title="Setup syllabus" onPress={() => nav.navigate('CourseSetup', { courseId: item.id })} />
              </View>
            </View>
          );
        }}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#0b1220' },
  header: { padding: 16, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  h1: { fontSize: 24, fontWeight: '800', color: 'white' },
  row: { paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center' },
  input: {
    flex: 1,
    backgroundColor: '#121a2b',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: 'white',
    borderWidth: 1,
    borderColor: '#1f2a43',
  },
  card: {
    backgroundColor: '#121a2b',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1f2a43',
    marginBottom: 12,
  },
  cardSelected: { borderColor: '#4c7dff' },
  cardTitle: { color: 'white', fontSize: 18, fontWeight: '700' },
  cardMeta: { color: '#8ea0c7', marginTop: 6 },
  cardButtons: { flexDirection: 'row', marginTop: 12, alignItems: 'center' },
});


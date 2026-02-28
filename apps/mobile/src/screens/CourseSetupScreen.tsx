import React, { useEffect, useState } from 'react';
import { Button, FlatList, SafeAreaView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { RouteProp, useRoute } from '@react-navigation/native';

import { apiFetch } from '../api/client';
import { useCourse } from '../course/CourseContext';

type Topic = {
  id: string;
  course_id: string;
  parent_id: string | null;
  title: string;
  order_index: number;
  is_leaf: boolean;
};

type Params = { courseId: string };

export function CourseSetupScreen() {
  const route = useRoute<RouteProp<Record<string, Params>, string>>();
  const courseId = (route.params as any)?.courseId as string;
  const { setCourseId } = useCourse();
  const [topics, setTopics] = useState<Topic[]>([]);
  const [title, setTitle] = useState('');
  const [parentId, setParentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      const data = (await apiFetch(`/courses/${courseId}/topics`)) as Topic[];
      setTopics(data);
      setCourseId(courseId);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId]);

  async function addTopic() {
    const t = title.trim();
    if (!t) return;
    await apiFetch(`/courses/${courseId}/topics`, {
      method: 'POST',
      body: JSON.stringify({ title: t, parent_id: parentId, order_index: topics.length }),
    });
    setTitle('');
    await refresh();
  }

  async function importCanvas() {
    await apiFetch(`/courses/${courseId}/import/canvas`, { method: 'POST' });
    await refresh();
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.header}>
        <Text style={styles.h1}>Syllabus</Text>
        <Button title="Canvas import (stub)" onPress={importCanvas} />
      </View>

      <View style={styles.row}>
        <TextInput
          style={styles.input}
          placeholder="Add topic/subtopic"
          placeholderTextColor="#8ea0c7"
          value={title}
          onChangeText={setTitle}
        />
        <View style={{ width: 10 }} />
        <Button title="Add" onPress={addTopic} />
      </View>

      <Text style={styles.parentHint}>
        Parent: {parentId ? topics.find((t) => t.id === parentId)?.title ?? parentId : 'None'} (tap a topic below to set)
      </Text>

      <FlatList
        data={topics}
        refreshing={loading}
        onRefresh={refresh}
        keyExtractor={(t) => t.id}
        contentContainerStyle={{ padding: 16 }}
        renderItem={({ item }) => (
          <TouchableOpacity onPress={() => setParentId(item.id)}>
            <View style={[styles.card, parentId === item.id && styles.cardSelected]}>
              <Text style={styles.cardTitle}>
                {item.parent_id ? '↳ ' : ''}{item.title}
              </Text>
              <Text style={styles.cardMeta}>{item.is_leaf ? 'Leaf (subtopic)' : 'Parent topic'}</Text>
            </View>
          </TouchableOpacity>
        )}
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
  parentHint: { paddingHorizontal: 16, paddingTop: 12, color: '#8ea0c7' },
  card: {
    backgroundColor: '#121a2b',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1f2a43',
    marginBottom: 12,
  },
  cardSelected: { borderColor: '#4c7dff' },
  cardTitle: { color: 'white', fontSize: 16, fontWeight: '700' },
  cardMeta: { color: '#8ea0c7', marginTop: 6 },
});


import React, { useEffect, useState } from 'react';
import { Button, FlatList, SafeAreaView, StyleSheet, Text, View } from 'react-native';

import { apiFetch } from '../api/client';
import { useCourse } from '../course/CourseContext';

type ProgressItem = {
  topic_id: string;
  mastery_score: number;
  last_seen_at: string | null;
  next_review_at: string | null;
};

export function ProgressScreen() {
  const { courseId } = useCourse();
  const [items, setItems] = useState<ProgressItem[]>([]);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    if (!courseId) return;
    setLoading(true);
    try {
      const data = (await apiFetch(`/progress?course_id=${courseId}`)) as { items: ProgressItem[] };
      setItems(data.items ?? []);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId]);

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.header}>
        <Text style={styles.h1}>Progress</Text>
        <Button title="Refresh" onPress={refresh} disabled={!courseId || loading} />
      </View>
      {!courseId ? <Text style={styles.meta}>Select a course first (Courses tab).</Text> : null}
      <FlatList
        data={items}
        keyExtractor={(i) => i.topic_id}
        contentContainerStyle={{ padding: 16 }}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{item.topic_id}</Text>
            <Text style={styles.cardMeta}>Mastery: {(item.mastery_score * 100).toFixed(0)}%</Text>
            <Text style={styles.cardMeta}>Next review: {item.next_review_at ?? '—'}</Text>
          </View>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#0b1220' },
  header: { padding: 16, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  h1: { fontSize: 24, fontWeight: '800', color: 'white' },
  meta: { paddingHorizontal: 16, color: '#8ea0c7' },
  card: {
    backgroundColor: '#121a2b',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1f2a43',
    marginBottom: 12,
  },
  cardTitle: { color: 'white', fontSize: 12, fontWeight: '700' },
  cardMeta: { color: '#8ea0c7', marginTop: 6 },
});


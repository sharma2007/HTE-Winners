import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Button, Dimensions, Modal, SafeAreaView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Video, ResizeMode } from 'expo-av';
import Animated, { useAnimatedScrollHandler, useSharedValue } from 'react-native-reanimated';

import { apiFetch } from '../api/client';
import { useCourse } from '../course/CourseContext';

type Reel = {
  id: string;
  topic_id: string;
  video_url: string;
  captions_vtt: string | null;
  duration_sec: number;
};

type Quiz = {
  id: string;
  topic_id: string;
  question: string;
  choices: string[] | null;
};

const { height: SCREEN_H } = Dimensions.get('window');
const N_REELS_PER_QUIZ = 3;

function captionFromVtt(vtt: string | null) {
  if (!vtt) return '';
  const lines = vtt
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l && !l.includes('-->') && l !== 'WEBVTT');
  return lines.slice(0, 2).join(' ');
}

export function FeedScreen() {
  const { courseId } = useCourse();
  const [reels, setReels] = useState<Reel[]>([]);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [quizVisible, setQuizVisible] = useState(false);
  const [reelIndex, setReelIndex] = useState(0);
  const videoRefs = useRef<Record<string, Video | null>>({});
  const lastIndexRef = useRef(0);
  const lastSwitchAtRef = useRef<number>(Date.now());

  const scrollY = useSharedValue(0);
  const onScroll = useAnimatedScrollHandler({
    onScroll: (e) => {
      scrollY.value = e.contentOffset.y;
    },
  });

  async function refresh() {
    if (!courseId) return;
    const data = (await apiFetch(`/feed?course_id=${courseId}&limit=20`)) as { reels: Reel[]; quiz: Quiz | null };
    setReels(data.reels ?? []);
    setQuiz(data.quiz ?? null);
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId]);

  useEffect(() => {
    (async () => {
      const r = reels[reelIndex];
      if (!r) return;

      // Log watch event for previous reel (lightweight).
      if (courseId && reelIndex !== lastIndexRef.current) {
        const prev = reels[lastIndexRef.current];
        const watchTimeSec = (Date.now() - lastSwitchAtRef.current) / 1000;
        if (prev) {
          await apiFetch('/events/watch', {
            method: 'POST',
            body: JSON.stringify({
              course_id: courseId,
              reel_id: prev.id,
              topic_id: prev.topic_id,
              event_type: watchTimeSec < 1.0 ? 'skip' : 'watch',
              watch_time_sec: watchTimeSec,
            }),
          }).catch(() => {});
        }
        lastIndexRef.current = reelIndex;
        lastSwitchAtRef.current = Date.now();
      }

      for (const [id, ref] of Object.entries(videoRefs.current)) {
        if (!ref) continue;
        if (id === r.id) await ref.playAsync().catch(() => {});
        else await ref.pauseAsync().catch(() => {});
      }
      if (reelIndex > 0 && reelIndex % N_REELS_PER_QUIZ === 0 && quiz) {
        setQuizVisible(true);
      }
    })();
  }, [reelIndex, reels, quiz, courseId]);

  const viewabilityConfig = useMemo(() => ({ itemVisiblePercentThreshold: 80 }), []);
  const onViewableItemsChanged = useRef(({ viewableItems }: any) => {
    if (viewableItems?.length) setReelIndex(viewableItems[0].index ?? 0);
  }).current;

  async function submitQuiz(correct: boolean, selected: any) {
    if (!courseId || !quiz) return;
    await apiFetch('/events/quiz_result', {
      method: 'POST',
      body: JSON.stringify({ course_id: courseId, quiz_id: quiz.id, topic_id: quiz.topic_id, correct, selected }),
    });
    setQuizVisible(false);
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.headerOverlay} pointerEvents="box-none">
        <View style={styles.headerInner}>
          <Text style={styles.h1}>Focus Feed</Text>
          <Button title="Refresh" onPress={refresh} disabled={!courseId} />
        </View>
        {!courseId ? <Text style={styles.meta}>Select a course first (Courses tab).</Text> : null}
      </View>

      <Animated.FlatList
        data={reels}
        keyExtractor={(r) => r.id}
        pagingEnabled
        snapToInterval={SCREEN_H}
        snapToAlignment="start"
        decelerationRate="fast"
        showsVerticalScrollIndicator={false}
        onScroll={onScroll}
        scrollEventThrottle={16}
        viewabilityConfig={viewabilityConfig}
        onViewableItemsChanged={onViewableItemsChanged}
        renderItem={({ item }) => (
          <View style={[styles.reelContainer, { height: SCREEN_H }]}>
            <Video
              ref={(r) => {
                videoRefs.current[item.id] = r;
              }}
              style={styles.video}
              source={{ uri: item.video_url }}
              resizeMode={ResizeMode.COVER}
              isLooping
              shouldPlay={false}
            />
            <View style={styles.actions}>
              <TouchableOpacity
                style={styles.actionBtn}
                onPress={() => {
                  if (!courseId) return;
                  apiFetch('/events/watch', {
                    method: 'POST',
                    body: JSON.stringify({
                      course_id: courseId,
                      reel_id: item.id,
                      topic_id: item.topic_id,
                      event_type: 'like',
                    }),
                  }).catch(() => {});
                }}
              >
                <Text style={styles.actionText}>Like</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionBtn}
                onPress={() => {
                  if (!courseId) return;
                  apiFetch('/events/watch', {
                    method: 'POST',
                    body: JSON.stringify({
                      course_id: courseId,
                      reel_id: item.id,
                      topic_id: item.topic_id,
                      event_type: 'save',
                    }),
                  }).catch(() => {});
                }}
              >
                <Text style={styles.actionText}>Save</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionBtn}
                onPress={() => {
                  if (!courseId) return;
                  apiFetch('/events/watch', {
                    method: 'POST',
                    body: JSON.stringify({
                      course_id: courseId,
                      reel_id: item.id,
                      topic_id: item.topic_id,
                      event_type: 'share',
                    }),
                  }).catch(() => {});
                }}
              >
                <Text style={styles.actionText}>Share</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.captionBox}>
              <Text style={styles.captionText} numberOfLines={3}>
                {captionFromVtt(item.captions_vtt) || '...'}
              </Text>
            </View>
          </View>
        )}
      />

      <Modal visible={quizVisible} transparent animationType="fade">
        <View style={styles.quizBackdrop}>
          <View style={styles.quizCard}>
            <Text style={styles.quizTitle}>Quick quiz</Text>
            <Text style={styles.quizQ}>{quiz?.question}</Text>
            {(quiz?.choices ?? ['Got it']).map((c, idx) => (
              <TouchableOpacity key={idx} style={styles.choice} onPress={() => submitQuiz(idx === 0, idx)}>
                <Text style={styles.choiceText}>{c}</Text>
              </TouchableOpacity>
            ))}
            <View style={{ height: 10 }} />
            <Button title="Skip" onPress={() => setQuizVisible(false)} />
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#0b1220' },
  headerOverlay: { position: 'absolute', left: 0, right: 0, top: 0, zIndex: 10, paddingHorizontal: 16, paddingTop: 8 },
  headerInner: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  h1: { fontSize: 22, fontWeight: '800', color: 'white' },
  meta: { marginTop: 4, color: '#8ea0c7' },
  reelContainer: { width: '100%', backgroundColor: 'black' },
  video: { flex: 1 },
  actions: { position: 'absolute', right: 12, bottom: 220, gap: 10 },
  actionBtn: { backgroundColor: 'rgba(0,0,0,0.35)', paddingVertical: 10, paddingHorizontal: 12, borderRadius: 12 },
  actionText: { color: 'white', fontWeight: '700' },
  captionBox: {
    position: 'absolute',
    left: 16,
    right: 16,
    bottom: 120,
    backgroundColor: 'rgba(0,0,0,0.35)',
    padding: 12,
    borderRadius: 12,
  },
  captionText: { color: 'white', fontSize: 14, lineHeight: 18 },
  quizBackdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'center', padding: 24 },
  quizCard: { backgroundColor: '#121a2b', borderRadius: 16, padding: 16, borderWidth: 1, borderColor: '#1f2a43' },
  quizTitle: { color: 'white', fontSize: 18, fontWeight: '800' },
  quizQ: { color: '#b7c0d6', marginTop: 10, lineHeight: 18 },
  choice: { marginTop: 10, padding: 12, backgroundColor: '#0b1220', borderRadius: 12, borderWidth: 1, borderColor: '#1f2a43' },
  choiceText: { color: 'white' },
});


import React from 'react';
import { Button, SafeAreaView, StyleSheet, Text, View } from 'react-native';

import { useAuth } from '../auth/AuthContext';

export function SettingsScreen() {
  const { signOut } = useAuth();
  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <Text style={styles.h1}>Settings</Text>
        <Text style={styles.meta}>Reel length, review frequency, and voice persona can be wired here.</Text>
        <View style={{ height: 20 }} />
        <Button title="Sign out" onPress={signOut} />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#0b1220' },
  container: { flex: 1, padding: 24 },
  h1: { fontSize: 24, fontWeight: '800', color: 'white' },
  meta: { color: '#8ea0c7', marginTop: 8, lineHeight: 18 },
});


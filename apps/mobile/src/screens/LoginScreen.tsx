import React, { useEffect, useMemo, useState } from 'react';
import { Button, SafeAreaView, StyleSheet, Text, View } from 'react-native';
import * as AuthSession from 'expo-auth-session';

import { useAuth } from '../auth/AuthContext';

export function LoginScreen() {
  const { signInDev, signInWithGoogleIdToken } = useAuth();
  const discovery = AuthSession.useAutoDiscovery('https://accounts.google.com');

  const googleClientId = process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID;
  const redirectUri = AuthSession.makeRedirectUri();
  const nonce = useMemo(() => `${Date.now()}-${Math.random()}`, []);

  const [request, response, promptAsync] = AuthSession.useAuthRequest(
    {
      clientId: googleClientId ?? '',
      redirectUri,
      scopes: ['openid', 'profile', 'email'],
      responseType: AuthSession.ResponseType.IdToken,
      extraParams: { nonce },
    },
    discovery
  );

  useEffect(() => {
    (async () => {
      if (response?.type !== 'success') return;
      const idToken = (response.params as any)?.id_token;
      if (idToken) await signInWithGoogleIdToken(String(idToken));
    })();
  }, [response, signInWithGoogleIdToken]);

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <Text style={styles.title}>DoomLearn</Text>
        <Text style={styles.subtitle}>Replace doomscrolling with doom learning.</Text>

        <View style={styles.card}>
          <Button
            title="Continue with Google"
            onPress={() => promptAsync()}
            disabled={!request || !discovery || !googleClientId}
          />
          <View style={{ height: 12 }} />
          <Button title="Dev login (AUTH_MOCK)" onPress={signInDev} />
          {!googleClientId ? (
            <Text style={styles.hint}>
              Set EXPO_PUBLIC_GOOGLE_CLIENT_ID to enable Google OAuth (Dev login works locally).
            </Text>
          ) : null}
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#0b1220' },
  container: { flex: 1, padding: 24, justifyContent: 'center' },
  title: { fontSize: 44, fontWeight: '800', color: 'white', marginBottom: 8 },
  subtitle: { fontSize: 16, color: '#b7c0d6', marginBottom: 24 },
  card: {
    backgroundColor: '#121a2b',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1f2a43',
  },
  hint: { marginTop: 12, color: '#8ea0c7', fontSize: 12, lineHeight: 16 },
});


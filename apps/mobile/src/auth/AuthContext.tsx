import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

import { apiFetch, getToken, setToken } from '../api/client';

type AuthState = {
  token: string | null;
  loading: boolean;
  signInDev: () => Promise<void>;
  signInWithGoogleIdToken: (idToken: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const t = await getToken();
      setTokenState(t);
      setLoading(false);
    })();
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      token,
      loading,
      signInDev: async () => {
        const data = (await apiFetch('/auth/google', {
          method: 'POST',
          body: JSON.stringify({ id_token: 'dev' }),
        })) as { access_token: string };
        await setToken(data.access_token);
        setTokenState(data.access_token);
      },
      signInWithGoogleIdToken: async (idToken: string) => {
        const data = (await apiFetch('/auth/google', {
          method: 'POST',
          body: JSON.stringify({ id_token: idToken }),
        })) as { access_token: string };
        await setToken(data.access_token);
        setTokenState(data.access_token);
      },
      signOut: async () => {
        await setToken(null);
        setTokenState(null);
      },
    }),
    [token, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}


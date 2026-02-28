import React from 'react';
import { StatusBar } from 'expo-status-bar';

import { AuthProvider } from './src/auth/AuthContext';
import { CourseProvider } from './src/course/CourseContext';
import { AppNavigator } from './src/navigation/AppNavigator';

export default function App() {
  return (
    <AuthProvider>
      <CourseProvider>
        <StatusBar style="light" />
        <AppNavigator />
      </CourseProvider>
    </AuthProvider>
  );
}

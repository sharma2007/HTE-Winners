import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { useAuth } from '../auth/AuthContext';
import { LoginScreen } from '../screens/LoginScreen';
import { CoursesScreen } from '../screens/CoursesScreen';
import { CourseSetupScreen } from '../screens/CourseSetupScreen';
import { UploadScreen } from '../screens/UploadScreen';
import { FeedScreen } from '../screens/FeedScreen';
import { ProgressScreen } from '../screens/ProgressScreen';
import { SettingsScreen } from '../screens/SettingsScreen';

type CoursesStackParamList = {
  Courses: undefined;
  CourseSetup: { courseId: string };
};

const CoursesStack = createNativeStackNavigator<CoursesStackParamList>();
const Tab = createBottomTabNavigator();

function CoursesStackNavigator() {
  return (
    <CoursesStack.Navigator>
      <CoursesStack.Screen name="Courses" component={CoursesScreen} options={{ title: 'Courses' }} />
      <CoursesStack.Screen
        name="CourseSetup"
        component={CourseSetupScreen}
        options={{ title: 'Course setup' }}
      />
    </CoursesStack.Navigator>
  );
}

export function AppNavigator() {
  const { token } = useAuth();

  return (
    <NavigationContainer>
      {!token ? (
        <LoginScreen />
      ) : (
        <Tab.Navigator screenOptions={{ headerShown: false }}>
          <Tab.Screen name="CoursesTab" component={CoursesStackNavigator} options={{ title: 'Courses' }} />
          <Tab.Screen name="UploadTab" component={UploadScreen} options={{ title: 'Upload' }} />
          <Tab.Screen name="FeedTab" component={FeedScreen} options={{ title: 'Feed' }} />
          <Tab.Screen name="ProgressTab" component={ProgressScreen} options={{ title: 'Progress' }} />
          <Tab.Screen name="SettingsTab" component={SettingsScreen} options={{ title: 'Settings' }} />
        </Tab.Navigator>
      )}
    </NavigationContainer>
  );
}


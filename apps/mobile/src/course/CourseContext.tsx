import React, { createContext, useContext, useMemo, useState } from 'react';

type CourseState = {
  courseId: string | null;
  setCourseId: (id: string | null) => void;
};

const CourseContext = createContext<CourseState | null>(null);

export function CourseProvider({ children }: { children: React.ReactNode }) {
  const [courseId, setCourseId] = useState<string | null>(null);
  const value = useMemo(() => ({ courseId, setCourseId }), [courseId]);
  return <CourseContext.Provider value={value}>{children}</CourseContext.Provider>;
}

export function useCourse() {
  const ctx = useContext(CourseContext);
  if (!ctx) throw new Error('useCourse must be used within CourseProvider');
  return ctx;
}


// The five sections of the app and the screens each one lists. Plain data, so
// scripts/check-sections.mjs can load it with Node and prove every screen is reachable.
import type { ComponentProps } from 'react';
import type { Ionicons } from '@expo/vector-icons';

export interface SectionItem {
  icon: ComponentProps<typeof Ionicons>['name'];
  label: string;
  sub: string;
  route: string;
  color: string;
  /** Listed only when the profile records a female gender. */
  female?: boolean;
  devOnly?: boolean;
}

export interface Section {
  key: 'today' | 'body' | 'mind' | 'care' | 'community';
  title: string;
  blurb: string;
  icon: ComponentProps<typeof Ionicons>['name'];
  /** Tab route that shows the section's landing screen. */
  tab: string;
  searchable?: boolean;
  items: SectionItem[];
}

export const SECTIONS: Section[] = [
  {
    key: 'today', title: 'Today', blurb: 'Your call for the day and how you got here', icon: 'sunny-outline', tab: '/',
    items: [
      { icon: 'create-outline', label: 'Check-in', sub: 'Sleep, soreness, energy, stress', route: '/checkin', color: '#6366F1' },
      { icon: 'sunny-outline', label: 'Daily Briefing', sub: "Today's call from your data", route: '/coach', color: '#6366F1' },
      { icon: 'chatbubble-ellipses-outline', label: 'Coach chat', sub: 'Ask about training and recovery', route: '/chat', color: '#8B5CF6' },
      { icon: 'fitness-outline', label: 'Recovery', sub: 'Readiness breakdown', route: '/recovery-dashboard', color: '#EF4444' },
      { icon: 'grid-outline', label: 'Dashboard', sub: 'Everything at a glance', route: '/dashboard', color: '#6366F1' },
      { icon: 'trending-up', label: 'Trends', sub: 'HRV, load, readiness', route: '/trends', color: '#06B6D4' },
      { icon: 'bar-chart-outline', label: 'Stats', sub: 'Volume & PRs', route: '/stats', color: '#F97316' },
      { icon: 'analytics-outline', label: 'Analytics', sub: 'Patterns across your data', route: '/analytics', color: '#0EA5E9' },
      { icon: 'ribbon-outline', label: 'Achievements', sub: 'Badges, level & streaks', route: '/achievements', color: '#EAB308' },
      { icon: 'checkbox-outline', label: 'Habits', sub: 'Small daily wins', route: '/habits', color: '#14B8A6' },
      { icon: 'calendar-number-outline', label: 'Calendar', sub: 'Plan and history', route: '/health-calendar', color: '#06B6D4' },
      { icon: 'leaf-outline', label: 'Everyday Wellbeing', sub: 'Air quality, desk health, memory, travel', route: '/everyday', color: '#22C55E' },
    ],
  },
  {
    key: 'body', title: 'Body', blurb: 'Training, movement, sleep, vitals and food', icon: 'barbell-outline', tab: '/body-section',
    items: [
      { icon: 'barbell-outline', label: 'Train', sub: "Today's workout", route: '/workout', color: '#6366F1' },
      { icon: 'list-outline', label: 'Workouts', sub: 'Past and planned sessions', route: '/workouts', color: '#818CF8' },
      { icon: 'search', label: 'Exercises', sub: 'Movement library', route: '/exercises', color: '#6366F1' },
      { icon: 'calendar-outline', label: 'Periodization', sub: 'Long-term plan', route: '/periodization', color: '#06B6D4' },
      { icon: 'navigate-outline', label: 'Record a route', sub: 'Run, walk, ride or hike with GPS', route: '/run-record', color: '#22C55E' },
      { icon: 'videocam-outline', label: 'Form checker', sub: 'Camera feedback on your reps', route: '/form-checker', color: '#F97316' },
      { icon: 'body-outline', label: 'Posture', sub: 'Posture assessment', route: '/posture', color: '#0EA5E9' },
      { icon: 'scale-outline', label: 'Body', sub: 'Weight, measurements, goals & photos', route: '/body', color: '#F97316' },
      { icon: 'moon-outline', label: 'Sleep', sub: 'Stages & consistency', route: '/sleep', color: '#6366F1' },
      { icon: 'pulse-outline', label: 'HRV', sub: 'Readings & breathing coach', route: '/hrv', color: '#10B981' },
      { icon: 'heart-outline', label: 'Vital Signs', sub: 'Heart rate & blood pressure', route: '/vital-signs', color: '#EF4444' },
      { icon: 'camera-outline', label: 'Camera heart rate', sub: 'Fingertip over the lens and flash', route: '/camera-heart-rate', color: '#DC2626' },
      { icon: 'restaurant-outline', label: 'Nutrition', sub: 'Meals, macros, water & photo log', route: '/nutrition', color: '#F59E0B' },
      { icon: 'flask-outline', label: 'Precision Nutrition', sub: 'Food matched to your data', route: '/precision-nutrition', color: '#84CC16' },
      { icon: 'fast-food-outline', label: 'Recipes', sub: 'Meals that fit macros', route: '/recipes', color: '#F97316' },
      { icon: 'hourglass-outline', label: 'Longevity', sub: 'Long-term health markers', route: '/longevity', color: '#14B8A6' },
      { icon: 'mic-outline', label: 'Voice', sub: 'Voice log and voice health', route: '/voice-health', color: '#A855F7' },
    ],
  },
  {
    key: 'mind', title: 'Mind', blurb: 'Mood, stress, rest and habits of the mind', icon: 'bulb-outline', tab: '/mind-section',
    items: [
      { icon: 'bulb-outline', label: 'Mind', sub: 'Mood, journal & questionnaires', route: '/mental-health', color: '#A855F7' },
      { icon: 'water-outline', label: 'Wellness', sub: 'Breathing & meditation', route: '/wellness', color: '#06B6D4' },
      { icon: 'recording-outline', label: 'Sleep sounds', sub: 'Snoring and noise overnight', route: '/sleep-sounds', color: '#8B5CF6' },
      { icon: 'musical-notes-outline', label: 'Ambient', sub: 'Focus and calm soundscapes', route: '/ambient', color: '#6366F1' },
      { icon: 'time-outline', label: 'Circadian', sub: 'Light, timing and body clock', route: '/circadian', color: '#F59E0B' },
      { icon: 'hand-left-outline', label: 'Addiction recovery', sub: 'Streaks, triggers and support', route: '/addiction-recovery', color: '#22C55E' },
    ],
  },
  {
    key: 'care', title: 'Care', blurb: 'Programs for conditions, medicines and safety', icon: 'medkit-outline', tab: '/care-section', searchable: true,
    items: [
      { icon: 'shield-outline', label: 'Health', sub: 'Conditions & meds overview', route: '/health', color: '#22C55E' },
      { icon: 'pulse-outline', label: 'Health Hub', sub: 'Vitals & body systems', route: '/health-hub', color: '#22C55E' },
      { icon: 'clipboard-outline', label: 'Conditions & Recovery', sub: 'Check-ups, lab results, physio, falls', route: '/conditions', color: '#0EA5E9' },
      { icon: 'medical-outline', label: 'Medication', sub: 'Doses & reminders', route: '/medication', color: '#22C55E' },
      { icon: 'alarm-outline', label: 'Emergency', sub: 'Contacts & medical ID', route: '/emergency', color: '#DC2626' },
      { icon: 'medkit-outline', label: 'Care & Safety', sub: 'Care nearby, symptoms, first aid, schemes', route: '/care', color: '#EF4444' },
      { icon: 'water-outline', label: 'Cycle', sub: 'Phases & fertility window', route: '/cycle', color: '#EF4444', female: true },
      { icon: 'flower-outline', label: 'Fertility', sub: 'Tracking toward conception', route: '/fertility', color: '#EC4899', female: true },
      { icon: 'woman-outline', label: 'Pregnancy', sub: 'Trimester guidance', route: '/pregnancy', color: '#F472B6', female: true },
      { icon: 'speedometer-outline', label: 'Diabetes', sub: 'Glucose, meals and insulin log', route: '/diabetes', color: '#F59E0B' },
      { icon: 'heart-circle-outline', label: 'Cardiac rehab', sub: 'Guided return to exercise', route: '/cardiac-rehab', color: '#EF4444' },
      { icon: 'bandage-outline', label: 'Chronic pain', sub: 'Pain diary and pacing', route: '/chronic-pain', color: '#F97316' },
      { icon: 'cloud-outline', label: 'Respiratory', sub: 'Breathing training', route: '/respiratory', color: '#38BDF8' },
      { icon: 'sunny-outline', label: 'Skin health', sub: 'Spot photos and sun care', route: '/skin-health', color: '#FB923C' },
      { icon: 'scan-outline', label: 'Medical imaging', sub: 'ABCDE photo screening', route: '/medical-imaging', color: '#64748B' },
      { icon: 'git-branch-outline', label: 'Genomics', sub: 'What your report says', route: '/genomics', color: '#8B5CF6' },
      { icon: 'videocam-outline', label: 'Telemedicine', sub: 'Registered practitioners', route: '/telemedicine', color: '#0EA5E9' },
      { icon: 'radio-outline', label: 'Remote monitoring', sub: 'Readings shared with your carer', route: '/remote-monitoring', color: '#14B8A6' },
      { icon: 'wallet-outline', label: 'Health savings', sub: 'Costs, insurance and schemes', route: '/health-savings', color: '#22C55E' },
      { icon: 'globe-outline', label: 'Health equity', sub: 'Access and support near you', route: '/health-equity', color: '#6366F1' },
    ],
  },
  {
    key: 'community', title: 'Community', blurb: 'People you train and share with', icon: 'people-outline', tab: '/community-section',
    items: [
      { icon: 'people-outline', label: 'Community', sub: 'Challenges, leaderboard & feed', route: '/community', color: '#EC4899' },
      { icon: 'chatbubbles-outline', label: 'Forums', sub: 'Ask and answer', route: '/forums', color: '#8B5CF6' },
      { icon: 'heart-circle-outline', label: 'Family', sub: 'Private sharing with people you trust', route: '/family', color: '#EC4899' },
      { icon: 'play-circle-outline', label: 'Watch', sub: 'Videos and articles', route: '/content-feed', color: '#F97316' },
    ],
  },
];

/** Account, settings and legal screens, listed on the More tab. */
export const MORE: SectionItem[] = [
  { icon: 'resize-outline', label: 'Body & measurements', sub: 'Age, height, training preferences', route: '/personal-info', color: '#38BDF8' },
  { icon: 'settings-outline', label: 'App preferences', sub: 'Notifications, reminders', route: '/settings', color: '#818CF8' },
  { icon: 'watch-outline', label: 'Devices', sub: 'Health Connect, wearables & sync', route: '/devices', color: '#64748B' },
  { icon: 'lock-closed-outline', label: 'Privacy', sub: 'Consent and data choices', route: '/privacy', color: '#22C55E' },
  { icon: 'accessibility-outline', label: 'Accessibility', sub: 'Text size & motion', route: '/accessibility-settings', color: '#0EA5E9' },
  { icon: 'download-outline', label: 'Export Data', sub: 'Download your records', route: '/data-export', color: '#22C55E' },
  { icon: 'document-text-outline', label: 'Privacy policy', sub: 'How your data is handled', route: '/legal', color: '#94A3B8' },
  { icon: 'construct-outline', label: 'Dev Tools', sub: 'Your own AI key, reduce motion', route: '/dev-tools', color: '#94A3B8', devOnly: true },
];

/** Screens reached from inside a flow (sign-in, a running workout) rather than from a list. */
export const FLOW_SCREENS = ['login', 'register', 'onboarding', 'workout-detail', 'workout-active', 'workout-complete'];

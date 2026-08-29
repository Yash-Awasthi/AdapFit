/**
 * Smart Notification System — Medication reminders, emergency alerts,
 * health check-ins, and intelligent timing based on user patterns.
 */
import { Platform } from 'react-native';

// ─── Notification Types ───────────────────────────────────────
export type NotificationType =
  | 'medication_reminder'
  | 'emergency_alert'
  | 'health_checkin'
  | 'hydration_reminder'
  | 'sleep_reminder'
  | 'exercise_reminder'
  | 'meditation_reminder'
  | 'goal_progress'
  | 'challenge_update'
  | 'weekly_report'
  | 'achievement_unlocked'
  | 'streak_milestone'
  | 'appointment_reminder'
  | 'vital_alert'
  | 'care_team_message';

// ─── Notification Priority ────────────────────────────────────
export type NotificationPriority = 'low' | 'medium' | 'high' | 'critical';

// ─── Notification Interface ───────────────────────────────────
export interface HealthNotification {
  id: string;
  type: NotificationType;
  priority: NotificationPriority;
  title: string;
  body: string;
  data?: Record<string, any>;
  scheduledAt?: string;
  read: boolean;
  actionUrl?: string;
  icon?: string;
  color?: string;
}

// ─── Notification Templates ───────────────────────────────────
export const NOTIFICATION_TEMPLATES: Record<NotificationType, {
  icon: string;
  color: string;
  defaultPriority: NotificationPriority;
  titles: string[];
  bodies: string[];
}> = {
  medication_reminder: {
    icon: 'medical',
    color: '#EF4444',
    defaultPriority: 'high',
    titles: ['Time for Your Medication', 'Medication Reminder', 'Don\'t Forget Your Medicine'],
    bodies: [
      'It\'s time to take your {medication}. Stay consistent for best results.',
      'Your {medication} is due now. Tap to mark as taken.',
      'Reminder: Take {medication} ({dosage}) as prescribed.',
    ],
  },
  emergency_alert: {
    icon: 'alert-circle',
    color: '#DC2626',
    defaultPriority: 'critical',
    titles: ['Emergency Alert', 'Critical Health Alert', 'Immediate Attention Required'],
    bodies: [
      'Your {vital} reading ({value} {unit}) is outside normal range. Seek medical attention if concerned.',
      'Abnormal {vital} detected. Please check your condition.',
    ],
  },
  health_checkin: {
    icon: 'clipboard',
    color: '#6366F1',
    defaultPriority: 'medium',
    titles: ['Daily Health Check-in', 'How Are You Feeling?', 'Quick Health Update'],
    bodies: [
      'Take 30 seconds to log how you\'re feeling today.',
      'Your daily health check-in is ready. Let\'s see how you\'re doing!',
    ],
  },
  hydration_reminder: {
    icon: 'water',
    color: '#06B6D4',
    defaultPriority: 'low',
    titles: ['Hydration Reminder', 'Time to Drink Water', 'Stay Hydrated'],
    bodies: [
      'You\'ve had {current}/{goal} glasses today. Drink up!',
      'Water break! Your body needs hydration to stay at its best.',
    ],
  },
  sleep_reminder: {
    icon: 'moon',
    color: '#8B5CF6',
    defaultPriority: 'medium',
    titles: ['Bedtime Reminder', 'Wind Down for Sleep', 'Sleep Schedule'],
    bodies: [
      'It\'s {time} — start winding down for better sleep quality.',
      'Your bedtime is in {minutes} minutes. Consider putting away screens.',
    ],
  },
  exercise_reminder: {
    icon: 'fitness',
    color: '#F97316',
    defaultPriority: 'medium',
    titles: ['Workout Time', 'Move Your Body', 'Exercise Reminder'],
    bodies: [
      'You haven\'t exercised today. Even a 10-minute walk helps!',
      'Time to get moving! Your body will thank you.',
    ],
  },
  meditation_reminder: {
    icon: 'leaf',
    color: '#10B981',
    defaultPriority: 'low',
    titles: ['Meditation Time', 'Mindfulness Moment', 'Breathe & Relax'],
    bodies: [
      'Take 5 minutes for mindfulness meditation.',
      'A quick meditation session can reduce stress and improve focus.',
    ],
  },
  goal_progress: {
    icon: 'trophy',
    color: '#F59E0B',
    defaultPriority: 'medium',
    titles: ['Goal Update', 'Almost There!', 'Progress Alert'],
    bodies: [
      'You\'re {percent}% towards your {goal} goal. Keep going!',
      'Great progress! Just {remaining} more to reach your {goal} goal.',
    ],
  },
  challenge_update: {
    icon: 'flag',
    color: '#EC4899',
    defaultPriority: 'medium',
    titles: ['Challenge Update', 'Leaderboard Change', 'Challenge Activity'],
    bodies: [
      'You moved to #{rank} in the {challenge} challenge!',
      'Someone passed you in {challenge}. Log activity to stay ahead!',
    ],
  },
  weekly_report: {
    icon: 'bar-chart',
    color: '#6366F1',
    defaultPriority: 'medium',
    titles: ['Weekly Health Report', 'Your Week in Review', 'Health Summary Ready'],
    bodies: [
      'Your weekly health report is ready. Health score: {score}/100.',
      'See how you did this week across all health metrics.',
    ],
  },
  achievement_unlocked: {
    icon: 'ribbon',
    color: '#F59E0B',
    defaultPriority: 'low',
    titles: ['Achievement Unlocked!', 'New Badge Earned!', 'Congratulations!'],
    bodies: [
      'You earned the "{badge}" badge! Keep up the great work.',
    ],
  },
  streak_milestone: {
    icon: 'flame',
    color: '#EF4444',
    defaultPriority: 'low',
    titles: ['Streak Milestone!', 'Fire Streak!', 'Consistency Wins!'],
    bodies: [
      'You\'re on a {days}-day streak! Don\'t break the chain.',
    ],
  },
  appointment_reminder: {
    icon: 'calendar',
    color: '#6366F1',
    defaultPriority: 'high',
    titles: ['Appointment Reminder', 'Upcoming Appointment', 'Don\'t Forget Your Appointment'],
    bodies: [
      'You have an appointment with {doctor} at {time}. Prepare any questions beforehand.',
    ],
  },
  vital_alert: {
    icon: 'heart',
    color: '#EF4444',
    defaultPriority: 'high',
    titles: ['Vital Sign Alert', 'Health Warning', 'Abnormal Reading'],
    bodies: [
      'Your {vital} is {value} {unit} ({status}). Consider consulting your doctor.',
    ],
  },
  care_team_message: {
    icon: 'people',
    color: '#8B5CF6',
    defaultPriority: 'medium',
    titles: ['Message from Care Team', 'Provider Update', 'Health Team Message'],
    bodies: [
      'You have a new message from your care team.',
    ],
  },
};

// ─── Smart Notification Scheduler ─────────────────────────────
class SmartNotificationSystem {
  private notifications: HealthNotification[] = [];
  private userPreferences: Record<NotificationType, boolean> = {} as any;
  private quietHoursStart = 22; // 10 PM
  private quietHoursEnd = 7;   // 7 AM

  constructor() {
    Object.keys(NOTIFICATION_TEMPLATES).forEach(type => {
      this.userPreferences[type as NotificationType] = true;
    });
  }

  // Create a notification
  createNotification(type: NotificationType, overrides: Partial<HealthNotification> = {}): HealthNotification {
    const template = NOTIFICATION_TEMPLATES[type];
    const titleIndex = Math.floor(Math.random() * template.titles.length);
    const bodyIndex = Math.floor(Math.random() * template.bodies.length);

    const notification: HealthNotification = {
      id: `notif_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      type,
      priority: overrides.priority || template.defaultPriority,
      title: overrides.title || template.titles[titleIndex],
      body: overrides.body || template.bodies[bodyIndex],
      data: overrides.data,
      scheduledAt: overrides.scheduledAt,
      read: false,
      actionUrl: overrides.actionUrl,
      icon: overrides.icon || template.icon,
      color: overrides.color || template.color,
    };

    this.notifications.unshift(notification);
    return notification;
  }

  // Check if we should send (respects quiet hours)
  shouldSend(type: NotificationType): boolean {
    if (!this.userPreferences[type]) return false;
    const now = new Date();
    const hour = now.getHours();
    if (type !== 'emergency_alert' && type !== 'vital_alert') {
      if (hour >= this.quietHoursStart || hour < this.quietHoursEnd) return false;
    }
    return true;
  }

  // Get notifications
  getNotifications(limit = 50): HealthNotification[] {
    return this.notifications.slice(0, limit);
  }

  // Get unread count
  getUnreadCount(): number {
    return this.notifications.filter(n => !n.read).length;
  }

  // Mark as read
  markAsRead(id: string): void {
    const notif = this.notifications.find(n => n.id === id);
    if (notif) notif.read = true;
  }

  // Mark all as read
  markAllAsRead(): void {
    this.notifications.forEach(n => { n.read = true; });
  }

  // Toggle preference
  togglePreference(type: NotificationType): void {
    this.userPreferences[type] = !this.userPreferences[type];
  }

  // Get preferences
  getPreferences(): Record<NotificationType, boolean> {
    return { ...this.userPreferences };
  }

  // Set quiet hours
  setQuietHours(start: number, end: number): void {
    this.quietHoursStart = start;
    this.quietHoursEnd = end;
  }

  // Delete notification
  deleteNotification(id: string): void {
    this.notifications = this.notifications.filter(n => n.id !== id);
  }

  // Clear all
  clearAll(): void {
    this.notifications = [];
  }
}

export const notificationSystem = new SmartNotificationSystem();

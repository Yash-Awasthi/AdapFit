/**
 * AdapFit Push Notification Service
 * Uses expo-notifications for local and push notifications.
 */
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

// Configure notification handling
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export async function registerForPushNotifications(): Promise<string | null> {
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('recovery', {
      name: 'Recovery Alerts',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
    });

    await Notifications.setNotificationChannelAsync('workout', {
      name: 'Workout Reminders',
      importance: Notifications.AndroidImportance.DEFAULT,
    });
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    return null;
  }

  try {
    const token = await Notifications.getExpoPushTokenAsync();
    return token.data;
  } catch {
    return null;
  }
}

export async function scheduleRecoveryAlert(score: number, state: string) {
  let body = '';
  if (state === 'DEPLETED') {
    body = 'Your recovery is depleted. Consider a rest day.';
  } else if (state === 'REDUCED') {
    body = 'Recovery is low. Scale back intensity today.';
  } else if (state === 'MODERATE') {
    body = `Recovery at ${score}/100. Standard session OK.`;
  } else {
    body = `Great recovery (${score}/100). Push hard today!`;
  }

  await Notifications.scheduleNotificationAsync({
    content: {
      title: 'Morning Recovery Update',
      body,
      channelId: 'recovery',
    },
    trigger: null, // immediate
  });
}

export async function scheduleWorkoutReminder() {
  await Notifications.scheduleNotificationAsync({
    content: {
      title: 'Time to Train',
      body: 'Your adaptive workout is ready. Open AdapFit to start.',
      channelId: 'workout',
    },
    trigger: {
      hour: 9,
      minute: 0,
      repeats: true,
    },
  });
}

export async function cancelAllNotifications() {
  await Notifications.cancelAllScheduledNotificationsAsync();
}

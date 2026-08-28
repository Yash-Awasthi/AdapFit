/**
 * E2E Tests for AdapFit Core Flows
 * Uses Detox for React Native E2E testing
 *
 * Run: npx detox test --configuration android.emu.debug
 */

import { by, device, element, expect } from 'detox';

describe('AdapFit Core Flows', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true });
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it('should show onboarding screen', async () => {
    await expect(element(by.text('Welcome to AdapFit'))).toBeVisible();
  });

  it('should navigate through onboarding', async () => {
    // Complete onboarding steps
    await element(by.text('Get Started')).tap();
    await expect(element(by.text('What is your fitness level?'))).toBeVisible();

    await element(by.text('Intermediate')).tap();
    await element(by.text('Next')).tap();

    await expect(element(by.text('What are your goals?'))).toBeVisible();
    await element(by.text('Hypertrophy')).tap();
    await element(by.text('Complete')).tap();

    // Should land on recovery screen
    await expect(element(by.text('Recovery'))).toBeVisible();
  });

  it('should display recovery dashboard', async () => {
    // Skip onboarding if present
    try {
      await element(by.text('Get Started')).tap();
      await element(by.text('Skip')).tap();
    } catch {}

    await expect(element(by.text('Recovery'))).toBeVisible();
    await expect(element(by.text('Recovery Score'))).toBeVisible();
  });

  it('should generate a workout', async () => {
    try {
      await element(by.text('Get Started')).tap();
      await element(by.text('Skip')).tap();
    } catch {}

    // Navigate to workout tab
    await element(by.text('Workout')).tap();
    await expect(element(by.text('Workouts'))).toBeVisible();

    // Generate workout
    await element(by.text('Generate Adaptive Workout')).tap();
    await expect(element(by.text('Barbell Bench Press'))).toBeVisible();
  });

  it('should open AI coach chat', async () => {
    try {
      await element(by.text('Get Started')).tap();
      await element(by.text('Skip')).tap();
    } catch {}

    await element(by.text('Coach')).tap();
    await expect(element(by.text('AdapFit AI Coach'))).toBeVisible();

    // Send a message
    await element(by.text('Type a message...')).typeText('How am I doing?');
    await element(by.text('Send')).tap();

    // Should get a response
    await waitFor(element(by.text('response')))
      .toBeVisible()
      .withTimeout(10000);
  });

  it('should log a check-in', async () => {
    try {
      await element(by.text('Get Started')).tap();
      await element(by.text('Skip')).tap();
    } catch {}

    // Open check-in modal
    await element(by.text('Log Check-In')).tap();
    await expect(element(by.text('How are you feeling?'))).toBeVisible();

    // Fill in check-in
    await element(by.text('Soreness')).swipe('right', 'fast', 0.5);
    await element(by.text('Fatigue')).swipe('right', 'fast', 0.3);
    await element(by.text('Submit')).tap();

    await expect(element(by.text('Check-in logged'))).toBeVisible();
  });

  it('should display exercise catalog', async () => {
    try {
      await element(by.text('Get Started')).tap();
      await element(by.text('Skip')).tap();
    } catch {}

    await element(by.text('Exercises')).tap();
    await expect(element(by.text('Exercises'))).toBeVisible();

    // Filter by muscle
    await element(by.text('chest')).tap();
    await expect(element(by.text('Barbell Bench Press'))).toBeVisible();
  });

  it('should open form checker', async () => {
    try {
      await element(by.text('Get Started')).tap();
      await element(by.text('Skip')).tap();
    } catch {}

    await element(by.text('Workout')).tap();
    await element(by.text('Form Checker')).tap();

    await expect(element(by.text('Select an exercise'))).toBeVisible();
    await element(by.text('Squat')).tap();
    await expect(element(by.text('Simulate Rep'))).toBeVisible();
  });
});

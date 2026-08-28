import { api } from './api';

export interface QueuedItem {
  id: string;
  type: 'LOG_WORKOUT' | 'LOG_RECOVERY' | 'LOG_HYDRATION' | 'LOG_MOOD';
  payload: any;
  timestamp: number;
  retryCount: number;
}

class SyncQueueManager {
  private queue: QueuedItem[] = [];
  private isProcessing: boolean = false;

  constructor() {
    this.loadQueue();
  }

  private loadQueue() {
    try {
      // In-memory / localStorage fallback
      if (typeof window !== 'undefined' && window.localStorage) {
        const saved = window.localStorage.getItem('adapfit_sync_queue');
        if (saved) {
          this.queue = JSON.parse(saved);
        }
      }
    } catch (e) {
      console.warn('Failed to load sync queue from storage', e);
    }
  }

  private saveQueue() {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem('adapfit_sync_queue', JSON.stringify(this.queue));
      }
    } catch (e) {
      console.warn('Failed to save sync queue', e);
    }
  }

  public enqueue(type: QueuedItem['type'], payload: any): string {
    const id = `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const item: QueuedItem = {
      id,
      type,
      payload,
      timestamp: Date.now(),
      retryCount: 0,
    };
    this.queue.push(item);
    this.saveQueue();
    // Attempt processing immediately if online
    this.processQueue();
    return id;
  }

  public getQueueLength(): number {
    return this.queue.length;
  }

  public async processQueue(): Promise<{ processed: number; failed: number }> {
    if (this.isProcessing || this.queue.length === 0) {
      return { processed: 0, failed: 0 };
    }

    this.isProcessing = true;
    let processed = 0;
    let failed = 0;
    const remaining: QueuedItem[] = [];

    for (const item of this.queue) {
      try {
        switch (item.type) {
          case 'LOG_WORKOUT':
            await api.completeWorkout(item.payload.workout_id, item.payload);
            break;
          case 'LOG_RECOVERY':
            await api.createRecoveryLog(item.payload);
            break;
          case 'LOG_HYDRATION':
            await api.logHydration(item.payload.user_id, item.payload.amount_ml, item.payload.drink_type, item.payload.note);
            break;
          case 'LOG_MOOD':
            await api.logMood(item.payload);
            break;
        }
        processed++;
      } catch (err) {
        console.warn(`Sync queue item ${item.id} failed:`, err);
        item.retryCount++;
        if (item.retryCount < 5) {
          remaining.push(item);
        }
        failed++;
      }
    }

    this.queue = remaining;
    this.saveQueue();
    this.isProcessing = false;
    return { processed, failed };
  }
}

export const syncQueue = new SyncQueueManager();

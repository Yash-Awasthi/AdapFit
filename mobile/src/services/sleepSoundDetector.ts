/**
 * Snoring and noise detection from the microphone's level readings (dBFS), on the phone.
 *
 * Snoring is rhythmic: bursts of sound a breath apart (2.5 to 7 s), repeating.
 * A run of at least six such bursts with steady spacing is one snoring episode.
 * Other loud sounds are noise events. Levels are relative to the room's own
 * quiet level, measured as it goes, because phone microphones are not calibrated.
 *
 * Breathing pauses and talking are not reported: a room microphone's level
 * alone cannot tell them apart reliably, and a missing category is not scored.
 */

export type SnoringEpisode = { start_min: number; duration_min: number; bursts: number };
export type NoiseEvent = { at_min: number; above_quiet_db: number };
export type NightReport = {
  duration_minutes: number;
  snoring_events: SnoringEpisode[];
  noise_events: NoiseEvent[];
  quiet_level_dbfs: number | null;
};

const BURST_DB = 10; // above the quiet level
const NOISE_DB = 20;
const MERGE_GAP_MS = 600;
const MIN_BURST_MS = 300;
const MAX_BURST_MS = 3500;
const MIN_INTERVAL_MS = 2500;
const MAX_INTERVAL_MS = 7000;
const MIN_EPISODE_BURSTS = 6;
const MAX_INTERVAL_CV = 0.35;
const FLOOR_WINDOW = 240; // one reading per second kept for the floor: 4 minutes

type Burst = { start: number; end: number; peak: number };

export class SleepSoundDetector {
  private startedAt: number | null = null;
  private lastAt = 0;
  private analysedMs = 0;
  private floorSamples: number[] = [];
  private lastFloorAt = 0;
  private floor: number | null = null;
  private current: Burst | null = null;
  private run: Burst[] = [];
  private episodes: SnoringEpisode[] = [];
  private noise: NoiseEvent[] = [];
  private lastNoiseAt = -Infinity;

  /** One level reading. Gaps longer than 5 s (screen off, recorder restart) are not counted as listened time. */
  push(tMs: number, dbfs: number): void {
    if (!Number.isFinite(dbfs)) return;
    if (this.startedAt === null) this.startedAt = tMs;
    const gap = tMs - this.lastAt;
    if (this.lastAt && gap > 0 && gap < 5000) this.analysedMs += gap;
    this.lastAt = tMs;

    if (tMs - this.lastFloorAt >= 1000) {
      this.lastFloorAt = tMs;
      this.floorSamples.push(dbfs);
      if (this.floorSamples.length > FLOOR_WINDOW) this.floorSamples.shift();
      const sorted = [...this.floorSamples].sort((a, b) => a - b);
      this.floor = sorted[Math.floor(sorted.length * 0.2)];
    }
    if (this.floor === null || this.floorSamples.length < 30) return;

    const above = dbfs - this.floor;
    if (above >= BURST_DB) {
      if (this.current && tMs - this.current.end <= MERGE_GAP_MS) {
        this.current.end = tMs;
        this.current.peak = Math.max(this.current.peak, above);
      } else {
        this.closeBurst();
        this.current = { start: tMs, end: tMs, peak: above };
      }
    } else if (this.current && tMs - this.current.end > MERGE_GAP_MS) {
      this.closeBurst();
    }
  }

  private minutes(t: number): number {
    return Math.round(((t - (this.startedAt ?? t)) / 60000) * 10) / 10;
  }

  private closeBurst(): void {
    const b = this.current;
    this.current = null;
    if (!b) return;
    const len = b.end - b.start + 250;
    if (len < MIN_BURST_MS) return;
    if (len > MAX_BURST_MS) {
      this.closeRun();
      this.noiseEvent(b);
      return;
    }
    const prev = this.run[this.run.length - 1];
    if (prev) {
      const interval = b.start - prev.start;
      if (interval < MIN_INTERVAL_MS || interval > MAX_INTERVAL_MS) {
        this.closeRun();
      }
    }
    this.run.push(b);
  }

  private noiseEvent(b: Burst): void {
    if (b.peak < NOISE_DB || b.start - this.lastNoiseAt < 10000) return;
    this.lastNoiseAt = b.start;
    this.noise.push({ at_min: this.minutes(b.start), above_quiet_db: Math.round(b.peak) });
  }

  private closeRun(): void {
    const run = this.run;
    this.run = [];
    if (run.length >= MIN_EPISODE_BURSTS) {
      const intervals = run.slice(1).map((b, i) => b.start - run[i].start);
      const mean = intervals.reduce((a, x) => a + x, 0) / intervals.length;
      const sd = Math.sqrt(intervals.reduce((a, x) => a + (x - mean) ** 2, 0) / intervals.length);
      if (sd / mean <= MAX_INTERVAL_CV) {
        const start = run[0].start;
        const end = run[run.length - 1].end;
        this.episodes.push({ start_min: this.minutes(start), duration_min: Math.round(((end - start) / 60000) * 10) / 10, bursts: run.length });
        return;
      }
    }
    run.forEach((b) => this.noiseEvent(b));
  }

  report(): NightReport {
    this.closeBurst();
    this.closeRun();
    return {
      duration_minutes: Math.round(this.analysedMs / 60000),
      snoring_events: this.episodes,
      noise_events: this.noise,
      quiet_level_dbfs: this.floor === null ? null : Math.round(this.floor),
    };
  }
}

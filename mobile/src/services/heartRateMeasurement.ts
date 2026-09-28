/** Bluetooth SIG Heart Rate Measurement (0x2A37) parsing, kept free of native imports. */
export interface HeartRateReading {
  heartRate: number;
  rrIntervalsMs: number[];
  contactDetected: boolean | null;
}

/** Parses a Heart Rate Measurement (0x2A37) value per the Bluetooth SIG spec. */
export function parseHeartRateMeasurement(bytes: Uint8Array): HeartRateReading {
  const flags = bytes[0];
  const wideHeartRate = (flags & 0x01) !== 0;
  const contactSupported = (flags & 0x04) !== 0;
  const energyPresent = (flags & 0x08) !== 0;
  const rrPresent = (flags & 0x10) !== 0;

  let offset = 1;
  const heartRate = wideHeartRate ? bytes[offset] | (bytes[offset + 1] << 8) : bytes[offset];
  offset += wideHeartRate ? 2 : 1;
  if (energyPresent) offset += 2;

  const rrIntervalsMs: number[] = [];
  if (rrPresent) {
    for (; offset + 1 < bytes.length; offset += 2) {
      // RR is in units of 1/1024 s.
      rrIntervalsMs.push(Math.round(((bytes[offset] | (bytes[offset + 1] << 8)) * 1000) / 1024));
    }
  }
  return { heartRate, rrIntervalsMs, contactDetected: contactSupported ? (flags & 0x02) !== 0 : null };
}

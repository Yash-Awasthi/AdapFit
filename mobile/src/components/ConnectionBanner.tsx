import React, { useEffect, useState } from 'react';
import { Text, View } from 'react-native';
import { onReachabilityChange } from '../services/http';

/** Shown while the server cannot be reached, so empty screens are not mistaken for "no data". */
export function ConnectionBanner() {
  const [reachable, setReachable] = useState(true);
  useEffect(() => onReachabilityChange(setReachable), []);
  if (reachable) return null;
  return (
    <View accessibilityRole="alert" accessibilityLiveRegion="polite"
      style={{ position: 'absolute', bottom: 90, left: 16, right: 16, backgroundColor: '#7F1D1D', borderRadius: 10, padding: 12 }}>
      <Text style={{ color: '#FFF', fontSize: 14, fontWeight: '600' }}>Can't reach AdapFit</Text>
      <Text style={{ color: '#FDE2E2', fontSize: 13, marginTop: 2 }}>
        Check your connection. Screens may look empty until it's back; pull down to retry.
      </Text>
    </View>
  );
}

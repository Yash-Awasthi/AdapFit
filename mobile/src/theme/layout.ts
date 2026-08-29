/**
 * Responsive layout helpers.
 *
 * Screens previously read `Dimensions.get('window')` once at module load, which
 * is captured before the window is measured on some Android launches and never
 * updates on rotation or fold. These hooks track the live window instead.
 */
import { useWindowDimensions, PixelRatio, Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { spacing } from './index';

/** Bar content height, excluding the bottom safe-area inset. Matches (tabs)/_layout. */
export const TAB_BAR_CONTENT_HEIGHT = 58;

/**
 * Top padding for a screen that paints its own header under the transparent
 * navigator header. Has to clear the status bar plus the floating back
 * control, or the control lands on top of the screen's own title.
 */
export const SCREEN_HEADER_TOP = 96;

/**
 * Total height the absolutely positioned tab bar occupies.
 *
 * Anything anchored to the bottom of a tab screen — an input row, a floating
 * button, the end of a scroll list — must clear this or the bar sits on top
 * of it and swallows the touches.
 */
export function useTabBarHeight(): number {
  const insets = useSafeAreaInsets();
  return TAB_BAR_CONTENT_HEIGHT + Math.max(insets.bottom, Platform.OS === 'ios' ? 20 : 8);
}

/** Phone widths we design against; anything wider gets an extra column. */
const TABLET_MIN_WIDTH = 700;

export interface Grid {
  width: number;
  columns: number;
  gap: number;
  padding: number;
  /** Width of a single cell, already accounting for padding and gaps. */
  cell: number;
  isTablet: boolean;
}

/**
 * Cell width for an evenly spaced grid.
 *
 * Percentage widths ('47%') drift as the gap changes and leave a ragged last
 * row; deriving the pixel width from the container keeps columns flush.
 */
export function useGrid(preferredColumns = 2, gap: number = spacing.md): Grid {
  const { width } = useWindowDimensions();
  const isTablet = width >= TABLET_MIN_WIDTH;
  const columns = isTablet ? preferredColumns + 1 : preferredColumns;
  const padding = spacing.screenPadding;
  const available = width - padding * 2 - gap * (columns - 1);
  return {
    width,
    columns,
    gap,
    padding,
    cell: Math.floor(available / columns),
    isTablet,
  };
}

/**
 * Font size clamped to the user's accessibility text scale.
 *
 * Headlines and numeric readouts break their container once the OS text size
 * is turned up; this keeps them legible without letting them overflow.
 */
export function scaledFont(size: number, maxScale = 1.3): number {
  const scale = Math.min(PixelRatio.getFontScale(), maxScale);
  return Math.round(size * scale);
}

/**
 * Props that let a headline shrink rather than clip or wrap awkwardly.
 * Spread onto a <Text> that renders a metric or a single-line title.
 */
export function fitText(lines = 1) {
  return { numberOfLines: lines, adjustsFontSizeToFit: true, minimumFontScale: 0.75 } as const;
}

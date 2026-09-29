/** YYYY-MM-DD in the phone's time zone; toISOString() gives the UTC day, which is yesterday in India before 05:30. */
export function localDay(d: Date = new Date()): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

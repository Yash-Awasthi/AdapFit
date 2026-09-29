/** "1 workout", "2 workouts": the noun with an s unless the count is exactly one. */
export const plural = (n: number, noun: string): string => `${n} ${noun}${n === 1 ? '' : 's'}`;

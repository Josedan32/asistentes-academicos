export function relativeDate(isoTimestamp: string, now: Date = new Date()): string {
  const then = new Date(isoTimestamp);
  const startOfThen = Date.UTC(then.getUTCFullYear(), then.getUTCMonth(), then.getUTCDate());
  const startOfNow = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  const dayDiff = Math.round((startOfNow - startOfThen) / (1000 * 60 * 60 * 24));

  if (dayDiff <= 0) return "hoy";
  if (dayDiff === 1) return "ayer";
  return `${dayDiff} días`;
}

// Times are stored in UTC and always shown labelled as UTC.

const WEEK_FORMAT: Intl.DateTimeFormatOptions = { timeZone: "UTC", day: "numeric", month: "short" };

// "2026-11-23" -> "23 Nov"
export function formatWeek(isoDate: string): string {
  return new Date(`${isoDate}T00:00:00Z`).toLocaleDateString("en-GB", WEEK_FORMAT);
}

export function plural(count: number, one: string, many: string): string {
  return `${count} ${count === 1 ? one : many}`;
}

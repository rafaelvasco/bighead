/**
 * Utility functions for date formatting.
 * All dates are stored as UTC timestamps and converted to the user's local timezone for display.
 */

/**
 * Format a UTC ISO date string to the user's local timezone
 * @param isoDate - ISO 8601 date string (UTC)
 * @param options - Optional formatting options
 * @returns Formatted date string in user's local timezone
 */
export function formatDateToLocal(
  isoDate: string | undefined,
  options?: {
    includeTime?: boolean;
    includeDate?: boolean;
    dateStyle?: 'full' | 'long' | 'medium' | 'short';
    timeStyle?: 'full' | 'long' | 'medium' | 'short';
  }
): string {
  if (!isoDate) return 'Unknown date';

  // Parse the UTC timestamp
  const date = new Date(isoDate);
  if (isNaN(date.getTime())) return 'Invalid date';

  const {
    includeTime = true,
    includeDate = true,
    dateStyle = 'medium',
    timeStyle = 'short',
  } = options || {};

  const parts: string[] = [];

  // Format date part
  if (includeDate) {
    const datePart = date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
    parts.push(datePart);
  }

  // Format time part
  if (includeTime) {
    const timePart = date.toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
    parts.push(timePart);
  }

  return parts.join(' ');
}

/**
 * Format a date as relative time (e.g., "2 hours ago", "3 days ago")
 * @param isoDate - ISO 8601 date string (UTC)
 * @returns Relative time string
 */
export function formatRelativeTime(isoDate: string | undefined): string {
  if (!isoDate) return 'Unknown date';

  const date = new Date(isoDate);
  if (isNaN(date.getTime())) return 'Invalid date';

  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
  }
  if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
  }
  if (diffInSeconds < 604800) {
    const days = Math.floor(diffInSeconds / 86400);
    return `${days} day${days !== 1 ? 's' : ''} ago`;
  }
  if (diffInSeconds < 2592000) {
    const weeks = Math.floor(diffInSeconds / 604800);
    return `${weeks} week${weeks !== 1 ? 's' : ''} ago`;
  }
  if (diffInSeconds < 31536000) {
    const months = Math.floor(diffInSeconds / 2592000);
    return `${months} month${months !== 1 ? 's' : ''} ago`;
  }

  const years = Math.floor(diffInSeconds / 31536000);
  return `${years} year${years !== 1 ? 's' : ''} ago`;
}

/**
 * Get current UTC timestamp as ISO string
 * @returns ISO 8601 date string in UTC
 */
export function getCurrentUTCTimestamp(): string {
  return new Date().toISOString();
}

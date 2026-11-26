// The backend only ever puts one of these fixed codes in the URL, so unknown
// values fall back to the generic message instead of being shown.
const MESSAGES: Record<string, string> = {
  invalid_state: "That connection attempt was invalid or had already been used. Please try again.",
  installation_not_allowed:
    "That GitHub installation could not be connected. Install DevPulse on your own personal GitHub account.",
  github_unavailable: "GitHub is not responding right now. Please try again in a moment.",
  not_configured: "Connecting GitHub is not available yet because the DevPulse GitHub App is not set up.",
  failed: "Connecting GitHub failed. Please try again.",
};

export function connectErrorMessage(code: string | null): string | null {
  if (code === null) return null;
  return MESSAGES[code] ?? MESSAGES.failed;
}

const REASONS: Record<string, string> = {
  access_revoked:
    "DevPulse can no longer access your GitHub account. The DevPulse GitHub App may have been uninstalled.",
  permission_missing:
    "DevPulse is missing a read permission it needs (repositories or pull requests). Review the App's permissions on GitHub.",
  suspended: "The DevPulse GitHub App is suspended on your GitHub account.",
};

export function attentionReason(reason: string | null): string {
  return (reason !== null && REASONS[reason]) || "DevPulse could not use your GitHub connection.";
}

// Times are stored in UTC and always shown labelled as UTC.
export function formatUtc(iso: string): string {
  const text = new Date(iso).toLocaleString("en-GB", {
    timeZone: "UTC",
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
  return `${text} UTC`;
}

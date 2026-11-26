// The backend only ever puts one of these fixed codes in the sign-in URL, so
// unknown values fall back to the generic message instead of being shown.
const MESSAGES: Record<string, string> = {
  cancelled: "Sign-in was cancelled. You can try again whenever you are ready.",
  invalid_state: "That sign-in attempt was invalid or had already been used. Please try again.",
  github_unavailable: "GitHub is not responding right now. Please try again in a moment.",
  not_configured: "Sign-in is not available yet because GitHub has not been set up for DevPulse.",
  failed: "Sign-in failed. Please try again.",
};

export function signInErrorMessage(code: string | null): string | null {
  if (code === null) return null;
  return MESSAGES[code] ?? MESSAGES.failed;
}

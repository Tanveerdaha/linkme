/**
 * Google OAuth authorization-code redirect helpers (frontend).
 *
 * Flow:
 * 1. User clicks Continue with Google → redirect to Google
 * 2. Google redirects back to /auth/google/callback?code=...
 * 3. Frontend POSTs { code } to backend (client secret stays on server)
 */

const GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth";
const STATE_KEY = "linkme_google_oauth_state";

export function getGoogleClientId(): string {
  return process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID?.trim() || "";
}

/** Must match backend GOOGLE_REDIRECT_URI and Google Cloud Console. */
export function getGoogleRedirectUri(): string {
  const fromEnv = process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI?.trim();
  if (fromEnv) return fromEnv;
  if (typeof window !== "undefined") {
    return `${window.location.origin}/auth/google/callback`;
  }
  return "";
}

function createState(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

export function beginGoogleOAuthRedirect(): void {
  const clientId = getGoogleClientId();
  const redirectUri = getGoogleRedirectUri();
  if (!clientId || !redirectUri) {
    throw new Error("Google sign-in is not configured.");
  }

  const state = createState();
  sessionStorage.setItem(STATE_KEY, state);

  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: "code",
    scope: "openid email profile",
    access_type: "online",
    include_granted_scopes: "true",
    prompt: "select_account",
    state,
  });

  window.location.assign(`${GOOGLE_AUTH_URL}?${params.toString()}`);
}

export function consumeGoogleOAuthState(returnedState: string | null): boolean {
  const expected = sessionStorage.getItem(STATE_KEY);
  sessionStorage.removeItem(STATE_KEY);
  if (!expected || !returnedState) return false;
  return expected === returnedState;
}

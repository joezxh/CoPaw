declare const VITE_API_BASE_URL: string;
declare const TOKEN: string;

const AUTH_TOKEN_KEY = "copaw_auth_token";
const AUTH_DISABLED_KEY = "copaw_auth_disabled";

/**
 * Set whether auth is disabled (no authentication required).
 * Called by AuthGuard after checking /api/auth/status.
 */
export function setAuthDisabled(disabled: boolean): void {
  if (disabled) {
    sessionStorage.setItem(AUTH_DISABLED_KEY, "true");
  } else {
    sessionStorage.removeItem(AUTH_DISABLED_KEY);
  }
}

/**
 * Check if auth is disabled (no authentication required).
 * Used by request.ts to avoid 401 redirect loops when auth is off.
 */
export function isAuthDisabled(): boolean {
  return sessionStorage.getItem(AUTH_DISABLED_KEY) === "true";
}

/**
 * Get the full API URL with /api prefix
 * @param path - API path (e.g., "/models", "/skills", "/enterprise/auth/login")
 * @returns Full API URL (e.g., "http://localhost:8088/api/models" or "/api/models")
 */
export function getApiUrl(path: string): string {
  const base = VITE_API_BASE_URL || "";
  const apiPrefix = "/api";
  // Remove leading slash if present, then prepend /api
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  // Check if path already starts with /api to avoid duplication
  if (normalizedPath.startsWith("/api/")) {
    return `${base}${normalizedPath}`;
  }
  return `${base}${apiPrefix}${normalizedPath}`;
}

/**
 * Get the API token - checks localStorage first (auth login),
 * then falls back to the build-time TOKEN constant.
 * @returns API token string or empty string
 */
export function getApiToken(): string {
  const stored = localStorage.getItem(AUTH_TOKEN_KEY);
  if (stored) return stored;
  return typeof TOKEN !== "undefined" ? TOKEN : "";
}

/**
 * Store the auth token in localStorage after login.
 */
export function setAuthToken(token: string): void {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

/**
 * Remove the auth token from localStorage (logout / 401).
 */
export function clearAuthToken(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

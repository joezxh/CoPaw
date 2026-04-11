/**
 * Enterprise Auth API — login, register, logout, /me, password, MFA
 */
import { request } from "../request";

export interface LoginRequest {
  username: string;
  password: string;
  mfa_code?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  username: string;
  roles: string[];
}

export interface RegisterRequest {
  username: string;
  password: string;
  email?: string;
  display_name?: string;
}

export interface CurrentUser {
  user_id: string;
  username: string;
  roles: string[];
  jti: string;
}

export const enterpriseAuthApi = {
  login: (data: LoginRequest) =>
    request<LoginResponse>("/api/enterprise/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  register: (data: RegisterRequest) =>
    request<{ id: string; username: string; email?: string }>(
      "/api/enterprise/auth/register",
      { method: "POST", body: JSON.stringify(data) }
    ),

  logout: () =>
    request<{ detail: string }>("/api/enterprise/auth/logout", {
      method: "POST",
    }),

  me: () => request<CurrentUser>("/api/enterprise/auth/me"),

  changePassword: (data: { current_password: string; new_password: string }) =>
    request<{ detail: string }>("/api/enterprise/auth/password", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  setupMfa: () =>
    request<{ secret: string; otpauth_url: string }>(
      "/api/enterprise/auth/mfa/setup",
      { method: "POST" }
    ),

  verifyMfa: (data: { secret: string; code: string }) =>
    request<{ detail: string }>("/api/enterprise/auth/mfa/verify", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

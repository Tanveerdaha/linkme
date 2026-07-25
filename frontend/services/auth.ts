import api from "@/services/api";
import type { AuthUser, LoginResponse, SignupResponse } from "@/types";

export type SignupPayload = {
  email: string;
  username: string;
  password: string;
  first_name: string;
  last_name: string;
};

export type LoginPayload = {
  login: string;
  password: string;
};

export async function signup(payload: SignupPayload): Promise<SignupResponse> {
  const { data } = await api.post<SignupResponse>("/auth/signup/", payload);
  return data;
}

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>("/auth/login/", payload);
  return data;
}

export async function loginWithGoogle(payload: {
  code?: string;
  token?: string;
}): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>("/auth/google/", payload);
  return data;
}

export type PhoneSendResponse = {
  phone_number: string;
  message: string;
  resend_available_in: number;
  expires_in: number;
};

export async function sendPhoneOtp(phone_number: string): Promise<PhoneSendResponse> {
  const { data } = await api.post<PhoneSendResponse>("/auth/phone/send/", { phone_number });
  return data;
}

export async function verifyPhoneOtp(
  phone_number: string,
  code: string,
): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>("/auth/phone/verify/", {
    phone_number,
    code,
  });
  return data;
}

export async function logout(refresh: string): Promise<void> {
  await api.post("/auth/logout/", { refresh });
}

export async function refreshToken(refresh: string): Promise<{ access: string; refresh?: string }> {
  const { data } = await api.post<{ access: string; refresh?: string }>("/auth/token/refresh/", {
    refresh,
  });
  return data;
}

export async function verifyEmail(token: string): Promise<{ message: string; email: string }> {
  const { data } = await api.get<{ message: string; email: string }>(
    `/auth/verify-email/${encodeURIComponent(token)}/`,
  );
  return data;
}

export async function requestPasswordReset(email: string): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>("/auth/password-reset/", { email });
  return data;
}

export async function confirmPasswordReset(
  token: string,
  password: string,
): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>("/auth/password-reset-confirm/", {
    token,
    password,
  });
  return data;
}

export {
  getMeProfile,
  updateMeProfile,
  getPublicProfile,
} from "@/services/profile";

export type { AuthUser };

import { z } from "zod";

const usernameRegex = /^[a-z0-9._]+$/;
const reservedUsernames = new Set(["admin", "support", "linkme", "root", "official"]);

export const loginSchema = z.object({
  login: z.string().min(1, "Email or username is required"),
  password: z.string().min(1, "Password is required"),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

const e164Regex = /^\+[1-9]\d{7,14}$/;

export function normalizePhoneInput(value: string): string {
  let cleaned = value.trim().replace(/[\s\-().]/g, "");
  if (cleaned.startsWith("00")) cleaned = `+${cleaned.slice(2)}`;
  if (!cleaned.startsWith("+") && /^\d+$/.test(cleaned)) cleaned = `+${cleaned}`;
  return cleaned;
}

export const phoneSchema = z.object({
  phone_number: z
    .string()
    .trim()
    .min(1, "Phone number is required")
    .transform(normalizePhoneInput)
    .refine((value) => e164Regex.test(value), {
      message: "Use international format with country code (e.g. +923001234567)",
    }),
});

export type PhoneFormValues = z.infer<typeof phoneSchema>;

export const phoneOtpSchema = z.object({
  code: z
    .string()
    .trim()
    .regex(/^\d{6}$/, "Enter the 6-digit code"),
});

export type PhoneOtpFormValues = z.infer<typeof phoneOtpSchema>;

export const signupSchema = z
  .object({
    first_name: z.string().min(1, "First name is required").max(150),
    last_name: z.string().min(1, "Last name is required").max(150),
    username: z
      .string()
      .min(3, "Username must be at least 3 characters")
      .max(30, "Username must be at most 30 characters")
      .regex(usernameRegex, "Only lowercase letters, numbers, _ and . allowed")
      .refine((value) => !reservedUsernames.has(value.toLowerCase()), {
        message: "This username is reserved",
      }),
    email: z.email("Enter a valid email"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string().min(1, "Confirm your password"),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export type SignupFormValues = z.infer<typeof signupSchema>;

export const forgotPasswordSchema = z.object({
  email: z.email("Enter a valid email"),
});

export type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

export const resetPasswordSchema = z
  .object({
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string().min(1, "Confirm your password"),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;

export const profileUpdateSchema = z.object({
  username: z
    .string()
    .min(3, "Username must be at least 3 characters")
    .max(30, "Username must be at most 30 characters")
    .regex(usernameRegex, "Only lowercase letters, numbers, _ and . allowed")
    .refine((value) => !reservedUsernames.has(value.toLowerCase()), {
      message: "This username is reserved",
    })
    .optional(),
  first_name: z.string().max(150).optional(),
  last_name: z.string().max(150).optional(),
  bio: z.string().max(2000).optional(),
  headline: z.string().max(200).optional(),
  location: z.string().max(120).optional(),
  website: z.union([z.url(), z.literal("")]).optional(),
  interests: z.string().optional(),
  pronouns: z.string().max(50).optional(),
  profile_visibility: z.enum(["PUBLIC", "PRIVATE"]).optional(),
  connection_visibility: z.enum(["PUBLIC", "PRIVATE", "CONNECTIONS_ONLY"]).optional(),
});

export type ProfileUpdateFormValues = z.infer<typeof profileUpdateSchema>;

/** Simple client-side password strength: 0–4. */
export function passwordStrength(password: string): number {
  let score = 0;
  if (password.length >= 8) score += 1;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;
  return score;
}

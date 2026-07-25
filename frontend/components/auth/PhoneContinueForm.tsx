"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getApiErrorMessage } from "@/services/api";
import { sendPhoneOtp } from "@/services/auth";
import { phoneSchema, type PhoneFormValues } from "@/types/forms";

type PhoneContinueFormProps = {
  redirectTo?: string;
};

export function PhoneContinueForm({ redirectTo = "/auth/phone/verify" }: PhoneContinueFormProps) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PhoneFormValues>({
    resolver: zodResolver(phoneSchema),
    defaultValues: { phone_number: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    setSubmitting(true);
    try {
      const result = await sendPhoneOtp(values.phone_number.trim());
      toast.success(result.message || "Verification code sent");
      const params = new URLSearchParams({
        phone: result.phone_number,
        resend: String(result.resend_available_in ?? 120),
      });
      router.push(`${redirectTo}?${params.toString()}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Unable to send verification code"));
    } finally {
      setSubmitting(false);
    }
  });

  return (
    <form onSubmit={onSubmit} className="space-y-3" noValidate>
      <div className="space-y-1.5">
        <label htmlFor="phone_number" className="text-sm font-medium">
          Phone number
        </label>
        <Input
          id="phone_number"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          placeholder="+923001234567"
          {...register("phone_number")}
        />
        {errors.phone_number ? (
          <p className="text-xs text-destructive">{errors.phone_number.message}</p>
        ) : (
          <p className="text-xs text-muted-foreground">
            Use international format with country code (WhatsApp).
          </p>
        )}
      </div>
      <Button className="w-full" type="submit" disabled={submitting}>
        {submitting ? "Sending code…" : "Continue with phone"}
      </Button>
    </form>
  );
}

import { GuestRoute } from "@/components/auth/GuestRoute";
import { SiteHeader } from "@/components/layout/site-header";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <GuestRoute>{children}</GuestRoute>
    </div>
  );
}

import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { SiteHeader } from "@/components/layout/site-header";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="page-container relative z-[1] min-h-screen">
      <SiteHeader />
      <ProtectedRoute>{children}</ProtectedRoute>
    </div>
  );
}

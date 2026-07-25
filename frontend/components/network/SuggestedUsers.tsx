"use client";

import { useQuery } from "@tanstack/react-query";

import { ConnectionButton } from "@/components/network/ConnectionButton";
import { NetworkCard } from "@/components/network/NetworkCard";
import { Loader } from "@/components/ui/loader";
import { getNetworkSuggestions } from "@/services/network";

type NetworkSuggestedUsersProps = {
  title?: string;
  className?: string;
};

export function NetworkSuggestedUsers({
  title = "People you may know",
  className,
}: NetworkSuggestedUsersProps) {
  const { data, isLoading } = useQuery({
    queryKey: ["network-discover"],
    queryFn: getNetworkSuggestions,
  });

  if (isLoading) {
    return (
      <div className={className}>
        <Loader label="Loading suggestions" />
      </div>
    );
  }

  if (!data?.length) return null;

  return (
    <section className={className}>
      <h2 className="font-[family-name:var(--font-fraunces)] text-lg font-semibold">
        {title}
      </h2>
      <ul className="mt-3 space-y-2">
        {data.map((user) => (
          <li key={user.username}>
            <NetworkCard
              user={user}
              subtitle={user.headline}
              meta={user.reason}
              actions={<ConnectionButton username={user.username} size="sm" />}
            />
          </li>
        ))}
      </ul>
    </section>
  );
}

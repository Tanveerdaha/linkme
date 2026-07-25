"use client";

import { useQuery } from "@tanstack/react-query";

import { getHealth } from "@/services/api";

/** Example React Query hook against the health endpoint. */
export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    retry: false,
  });
}

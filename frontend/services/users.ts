import api from "@/services/api";

export type UsernameAvailabilityResponse = {
  username: string;
  available: boolean;
  reason?: string;
};

export async function checkUsernameAvailability(
  username: string,
): Promise<UsernameAvailabilityResponse> {
  const { data } = await api.get<UsernameAvailabilityResponse>("/users/check-username/", {
    params: { username },
  });
  return data;
}

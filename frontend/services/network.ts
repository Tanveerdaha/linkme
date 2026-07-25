import api from "@/services/api";
import type { PageResult } from "@/types";

export type ConnectionStatusValue =
  | "NONE"
  | "REQUEST_SENT"
  | "REQUEST_RECEIVED"
  | "CONNECTED"
  | "BLOCKED";

export type ConnectionStatus = {
  status: ConnectionStatusValue;
  can_connect: boolean;
  connection_id?: string | null;
  is_self?: boolean;
};

export type NetworkUser = {
  username: string;
  name: string;
  avatar: string | null;
  headline: string;
};

export type ConnectionListItem = NetworkUser & {
  connected_at: string | null;
};

export type ConnectionRequest = {
  id: string;
  user: NetworkUser;
  message?: string;
  created_at: string;
};

export type DiscoverUser = NetworkUser & {
  reason: string;
};

export type NetworkSummary = {
  connections: number;
  requests_received: number;
  requests_sent: number;
  suggestions: number;
};

export type MutualConnections = {
  count: number;
  users: NetworkUser[];
};

export async function getNetworkSummary(): Promise<NetworkSummary> {
  const { data } = await api.get<NetworkSummary>("/network/");
  return data;
}

export async function getConnectionStatus(username: string): Promise<ConnectionStatus> {
  const { data } = await api.get<ConnectionStatus>(`/network/status/${username}/`);
  return data;
}

export async function sendConnectionRequest(
  username: string,
  message = "",
): Promise<ConnectionStatus> {
  const { data } = await api.post<ConnectionStatus>(`/network/request/${username}/`, {
    message,
  });
  return data;
}

export async function acceptRequest(requestId: string): Promise<ConnectionStatus> {
  const { data } = await api.post<ConnectionStatus>(
    `/network/request/${requestId}/accept/`,
  );
  return data;
}

export async function rejectRequest(requestId: string): Promise<ConnectionStatus> {
  const { data } = await api.post<ConnectionStatus>(
    `/network/request/${requestId}/reject/`,
  );
  return data;
}

export async function cancelRequest(requestId: string): Promise<ConnectionStatus> {
  const { data } = await api.delete<ConnectionStatus>(`/network/request/${requestId}/`);
  return data;
}

export async function getConnections(params?: {
  search?: string;
  page?: number;
  username?: string;
}): Promise<PageResult<ConnectionListItem>> {
  const { data } = await api.get<PageResult<ConnectionListItem>>("/network/connections/", {
    params,
  });
  return data;
}

export async function removeConnection(username: string): Promise<ConnectionStatus> {
  const { data } = await api.delete<ConnectionStatus>(
    `/network/connections/${username}/`,
  );
  return data;
}

export async function getReceivedRequests(): Promise<ConnectionRequest[]> {
  const { data } = await api.get<ConnectionRequest[]>("/network/requests/received/");
  return data;
}

export async function getSentRequests(): Promise<ConnectionRequest[]> {
  const { data } = await api.get<ConnectionRequest[]>("/network/requests/sent/");
  return data;
}

export async function getNetworkSuggestions(): Promise<DiscoverUser[]> {
  const { data } = await api.get<DiscoverUser[]>("/network/discover/");
  return data;
}

export async function getMutualConnections(username: string): Promise<MutualConnections> {
  const { data } = await api.get<MutualConnections>(`/network/mutual/${username}/`);
  return data;
}

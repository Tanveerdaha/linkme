import { create } from "zustand";

import * as networkApi from "@/services/network";
import type {
  ConnectionListItem,
  ConnectionRequest,
  ConnectionStatus,
  DiscoverUser,
  NetworkSummary,
} from "@/services/network";

type NetworkState = {
  summary: NetworkSummary | null;
  connections: ConnectionListItem[];
  connectionsCount: number;
  received: ConnectionRequest[];
  sent: ConnectionRequest[];
  suggestions: DiscoverUser[];
  statusByUsername: Record<string, ConnectionStatus>;
  loading: boolean;
  loadSummary: () => Promise<void>;
  loadConnections: (search?: string) => Promise<void>;
  loadRequests: () => Promise<void>;
  loadSuggestions: () => Promise<void>;
  fetchStatus: (username: string) => Promise<ConnectionStatus>;
  sendRequest: (username: string) => Promise<void>;
  acceptRequest: (requestId: string, username: string) => Promise<void>;
  rejectRequest: (requestId: string, username: string) => Promise<void>;
  cancelRequest: (requestId: string, username: string) => Promise<void>;
  removeConnection: (username: string) => Promise<void>;
  setStatus: (username: string, status: ConnectionStatus) => void;
};

export const useNetworkStore = create<NetworkState>((set) => ({
  summary: null,
  connections: [],
  connectionsCount: 0,
  received: [],
  sent: [],
  suggestions: [],
  statusByUsername: {},
  loading: false,
  loadSummary: async () => {
    const summary = await networkApi.getNetworkSummary();
    set({ summary });
  },
  loadConnections: async (search) => {
    set({ loading: true });
    try {
      const page = await networkApi.getConnections({ search, page: 1 });
      set({
        connections: page.results,
        connectionsCount: page.count,
        loading: false,
      });
    } catch (err) {
      set({ loading: false });
      throw err;
    }
  },
  loadRequests: async () => {
    const [received, sent] = await Promise.all([
      networkApi.getReceivedRequests(),
      networkApi.getSentRequests(),
    ]);
    set({ received, sent });
  },
  loadSuggestions: async () => {
    const suggestions = await networkApi.getNetworkSuggestions();
    set({ suggestions });
  },
  fetchStatus: async (username) => {
    const status = await networkApi.getConnectionStatus(username);
    set((state) => ({
      statusByUsername: { ...state.statusByUsername, [username]: status },
    }));
    return status;
  },
  sendRequest: async (username) => {
    const status = await networkApi.sendConnectionRequest(username);
    set((state) => ({
      statusByUsername: { ...state.statusByUsername, [username]: status },
    }));
  },
  acceptRequest: async (requestId, username) => {
    const status = await networkApi.acceptRequest(requestId);
    set((state) => ({
      received: state.received.filter((r) => r.id !== requestId),
      statusByUsername: { ...state.statusByUsername, [username]: status },
    }));
  },
  rejectRequest: async (requestId, username) => {
    const status = await networkApi.rejectRequest(requestId);
    set((state) => ({
      received: state.received.filter((r) => r.id !== requestId),
      statusByUsername: { ...state.statusByUsername, [username]: status },
    }));
  },
  cancelRequest: async (requestId, username) => {
    const status = await networkApi.cancelRequest(requestId);
    set((state) => ({
      sent: state.sent.filter((r) => r.id !== requestId),
      statusByUsername: { ...state.statusByUsername, [username]: status },
    }));
  },
  removeConnection: async (username) => {
    const status = await networkApi.removeConnection(username);
    set((state) => ({
      connections: state.connections.filter((c) => c.username !== username),
      connectionsCount: Math.max(0, state.connectionsCount - 1),
      statusByUsername: { ...state.statusByUsername, [username]: status },
    }));
  },
  setStatus: (username, status) => {
    set((state) => ({
      statusByUsername: { ...state.statusByUsername, [username]: status },
    }));
  },
}));

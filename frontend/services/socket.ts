/**
 * WebSocket clients for chat and notifications.
 */

type EventHandler = (payload: Record<string, unknown>) => void;

export function defaultWsBase(): string {
  if (typeof window === "undefined") return "ws://localhost:8013";
  if (process.env.NEXT_PUBLIC_WS_URL) return process.env.NEXT_PUBLIC_WS_URL;
  const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8013/api/v1";
  try {
    const url = new URL(api);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = "";
    url.search = "";
    url.hash = "";
    return url.toString().replace(/\/$/, "");
  } catch {
    return "ws://localhost:8013";
  }
}

class BaseSocket {
  protected socket: WebSocket | null = null;
  protected handlers = new Map<string, Set<EventHandler>>();
  protected heartbeatTimer: ReturnType<typeof setInterval> | null = null;

  protected bindSocket(url: string, heartbeatPayload?: Record<string, unknown>) {
    this.disconnect();
    this.socket = new WebSocket(url);

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as Record<string, unknown>;
        const type = String(data.type || "");
        this.emit(type, data);
        this.emit("*", data);
      } catch {
        // ignore malformed payloads
      }
    };

    this.socket.onopen = () => {
      this.emit("socket.open", {});
      if (heartbeatPayload) {
        this.heartbeatTimer = setInterval(() => {
          this.sendEvent(heartbeatPayload);
        }, 25_000);
      }
    };

    this.socket.onclose = () => {
      this.emit("socket.close", {});
      if (this.heartbeatTimer) {
        clearInterval(this.heartbeatTimer);
        this.heartbeatTimer = null;
      }
    };

    this.socket.onerror = () => {
      this.emit("socket.error", {});
    };
  }

  disconnect() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  sendEvent(payload: Record<string, unknown>) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(payload));
    }
  }

  subscribe(eventType: string, handler: EventHandler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler);
    return () => {
      this.handlers.get(eventType)?.delete(handler);
    };
  }

  get isConnected() {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  protected emit(eventType: string, payload: Record<string, unknown>) {
    this.handlers.get(eventType)?.forEach((handler) => handler(payload));
  }
}

export class ChatSocket extends BaseSocket {
  connect(conversationId: string, token: string) {
    const base = defaultWsBase();
    const url = `${base}/ws/chat/${conversationId}/?token=${encodeURIComponent(token)}`;
    this.bindSocket(url, { type: "presence.heartbeat" });
  }
}

export class NotificationSocket extends BaseSocket {
  connect(token: string) {
    const base = defaultWsBase();
    const url = `${base}/ws/notifications/?token=${encodeURIComponent(token)}`;
    this.bindSocket(url);
  }
}

let chatSingleton: ChatSocket | null = null;
let notificationSingleton: NotificationSocket | null = null;

export function connectSocket(conversationId: string, token: string): ChatSocket {
  if (!chatSingleton) chatSingleton = new ChatSocket();
  chatSingleton.connect(conversationId, token);
  return chatSingleton;
}

export function disconnectSocket() {
  chatSingleton?.disconnect();
}

export function sendEvent(payload: Record<string, unknown>) {
  chatSingleton?.sendEvent(payload);
}

export function subscribe(eventType: string, handler: EventHandler) {
  if (!chatSingleton) chatSingleton = new ChatSocket();
  return chatSingleton.subscribe(eventType, handler);
}

export function getChatSocket(): ChatSocket | null {
  return chatSingleton;
}

export function connectNotificationSocket(token: string): NotificationSocket {
  if (!notificationSingleton) notificationSingleton = new NotificationSocket();
  notificationSingleton.connect(token);
  return notificationSingleton;
}

export function disconnectNotificationSocket() {
  notificationSingleton?.disconnect();
}

export function subscribeNotifications(eventType: string, handler: EventHandler) {
  if (!notificationSingleton) notificationSingleton = new NotificationSocket();
  return notificationSingleton.subscribe(eventType, handler);
}

export function sendNotificationEvent(payload: Record<string, unknown>) {
  notificationSingleton?.sendEvent(payload);
}

export function getNotificationSocket(): NotificationSocket | null {
  return notificationSingleton;
}

export function handleNotification(
  payload: Record<string, unknown>,
  onNew: (notification: Record<string, unknown>) => void,
  onUnread?: (count: number) => void,
) {
  const type = String(payload.type || "");
  if (type === "notification.new" && payload.notification) {
    onNew(payload.notification as Record<string, unknown>);
  }
  if (type === "notification.unread_count" && onUnread) {
    onUnread(Number(payload.count || 0));
  }
}

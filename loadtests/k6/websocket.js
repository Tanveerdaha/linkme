/**
 * k6 WebSocket messaging load (up to 1000 concurrent connections).
 *
 * Requires a valid JWT:
 *   LINKME_ACCESS_TOKEN=<jwt> CONVERSATION_ID=<uuid> k6 run loadtests/k6/websocket.js
 */

import ws from "k6/ws";
import { check, sleep } from "k6";
import { Trend } from "k6/metrics";

const WS_BASE = __ENV.WS_URL || "ws://localhost:8000";
const TOKEN = __ENV.LINKME_ACCESS_TOKEN || "";
const CONVERSATION_ID = __ENV.CONVERSATION_ID || "";
const delivery = new Trend("ws_message_delivery", true);

export const options = {
  scenarios: {
    chat_connections: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 100 },
        { duration: "1m", target: 500 },
        { duration: "1m", target: 1000 },
        { duration: "30s", target: 0 },
      ],
    },
  },
  thresholds: {
    ws_message_delivery: ["p(95)<100"],
  },
};

export default function () {
  if (!TOKEN || !CONVERSATION_ID) {
    // Fall back to notifications socket smoke when chat params missing.
    const url = `${WS_BASE}/ws/notifications/?token=${TOKEN || "invalid"}`;
    const res = ws.connect(url, {}, function (socket) {
      socket.on("open", () => {
        sleep(2);
        socket.close();
      });
    });
    check(res, { "ws connected or rejected cleanly": (r) => r && r.status !== 0 });
    return;
  }

  const url = `${WS_BASE}/ws/chat/${CONVERSATION_ID}/?token=${TOKEN}`;
  const started = Date.now();
  const res = ws.connect(url, {}, function (socket) {
    socket.on("open", () => {
      socket.send(JSON.stringify({ type: "ping" }));
    });
    socket.on("message", () => {
      delivery.add(Date.now() - started);
    });
    socket.setTimeout(() => socket.close(), 5000);
  });
  check(res, { "chat ws ok": (r) => r && r.status === 101 });
  sleep(1);
}

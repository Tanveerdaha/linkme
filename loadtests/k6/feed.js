/**
 * k6 load / soak scripts for LinkMe.
 *
 * Feed browse (default):
 *   k6 run loadtests/k6/feed.js
 *
 * Messaging websocket (optional token):
 *   LINKME_ACCESS_TOKEN=... k6 run loadtests/k6/websocket.js
 *
 * Goals:
 *   API avg < 200ms · Feed p95 < 500ms · WS delivery < 100ms
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const BASE = __ENV.BASE_URL || "http://localhost:8000";
const feedLatency = new Trend("feed_latency", true);
const errorRate = new Rate("errors");

export const options = {
  scenarios: {
    feed_browse: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 50 },
        { duration: "1m", target: 200 },
        { duration: "2m", target: 500 },
        // Uncomment for 10k-user soak (requires substantial infra):
        // { duration: "5m", target: 10000 },
        { duration: "30s", target: 0 },
      ],
      gracefulRampDown: "30s",
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<500", "avg<200"],
    feed_latency: ["p(95)<500"],
    errors: ["rate<0.01"],
  },
};

export default function () {
  const res = http.get(`${BASE}/api/v1/feed/public/`);
  feedLatency.add(res.timings.duration);
  const ok = check(res, {
    "feed status 200": (r) => r.status === 200,
  });
  errorRate.add(!ok);
  sleep(1);
}

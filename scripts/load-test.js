import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    normal: {
      executor: 'constant-vus',
      vus: 10,
      duration: '30s',
      exec: 'normalTraffic',
      tags: { scenario: 'normal' },
    },
    stress: {
      executor: 'constant-vus',
      vus: 50,
      duration: '30s',
      exec: 'stressTraffic',
      startTime: '35s',
      tags: { scenario: 'stress' },
    },
    failure: {
      executor: 'constant-vus',
      vus: 10,
      duration: '20s',
      exec: 'failureTraffic',
      startTime: '70s',
      tags: { scenario: 'failure' },
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<1000'], // 95% of requests under 1s
    http_req_failed: ['rate<0.1'],     // Error rate under 10%
  },
};

const BASE_URL = 'http://localhost:8080';

export function normalTraffic() {
  const res = http.get(`${BASE_URL}/service-a/greet-service-b`);
  check(res, {
    'normal: status is 200': (r) => r.status === 200,
    'normal: response time < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(0.5);
}

export function stressTraffic() {
  const res = http.get(`${BASE_URL}/service-a/greet-service-b`);
  check(res, {
    'stress: status is 200': (r) => r.status === 200,
  });
  sleep(0.1);
}

export function failureTraffic() {
  // Mix of fail and slow endpoints
  const endpoints = [
    `${BASE_URL}/service-a/fail`,
    `${BASE_URL}/service-b/fail`,
    `${BASE_URL}/service-c/fail`,
    `${BASE_URL}/service-a/slow`,
    `${BASE_URL}/service-b/slow`,
  ];
  const url = endpoints[Math.floor(Math.random() * endpoints.length)];
  const res = http.get(url);
  check(res, {
    'failure: status is 4xx or 5xx': (r) => r.status >= 400,
  });
  sleep(0.3);
}

# Benchmark Report

## Test Tool
- **Tool**: k6
- **Version**: v2.0.0 (commit/8c3be52cc1, go1.26.3, linux/amd64)

## Test Command
```bash
k6 run scripts/load-test.js
Test Scenarios
Table
Scenario	VUs	Duration	Endpoint
Normal traffic	10	30s	/service-a/greet-service-b
Stress traffic	50	30s	/service-a/greet-service-b
Failure traffic	10	20s	/service-a/fail, /slow, etc.
Results
Overall
Table
Metric	Value
Total HTTP Requests	4,106
Total Checks	4,684
Checks Passed	99.67% (4,669/4,684)
Checks Failed	0.32% (15/4,684)
Avg Latency	351.74ms
p95 Latency	627.73ms
Error Rate	1.24% (51/4,106)
Normal Traffic
Table
Metric	Value
VUs	10
Duration	30s
Endpoint	/service-a/greet-service-b
Avg Latency	~285ms
p95 Latency	< 500ms
Error Rate	0%
Stress Traffic
Table
Metric	Value
VUs	50
Duration	30s
Endpoint	/service-a/greet-service-b
Avg Latency	~528ms
p95 Latency	~628ms
Error Rate	< 2%
Failure Traffic
Table
Metric	Value
VUs	10
Duration	20s
Endpoints	/fail, /slow
Avg Latency	N/A (mixed)
p95 Latency	N/A (mixed)
Error Rate	~23% (expected)
Metrics Observed
[x] Request rate increased under stress (50 VUs vs 10 VUs)
[x] Error rate spiked during failure scenario (controlled /fail endpoints)
[x] p95 latency degraded under stress (628ms vs 285ms baseline)
Alerts Triggered
[ ] ServiceDown — no services stopped during test
[ ] HighErrorRate — error rate stayed below 10% threshold
[ ] HighLatency — p95 stayed below 1s threshold
Traces Observed
Multi-service trace visible in Jaeger for /greet-service-b
Spans: service-a → service-b → service-c → callback to service-a
Error traces visible for /fail endpoints
Lessons Learned
System handles 10x normal load with acceptable latency (<1s p95)
Controlled failure endpoints correctly trigger 500 errors
Metrics, traces, and logs all correlate during load testing
Alert thresholds (10% error rate, 1s latency) are appropriate for this workload

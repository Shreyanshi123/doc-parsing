PRODUCTION INCIDENT REPORT
Incident INC-2026-042. Service Document Router API. Severity SEV-2.
Start 09:14 IST. Detection 09:17 IST. Mitigation 10:02 IST. Resolution 11:26 IST.
Impact: 17.4 percent of synthetic requests received HTTP 503 responses. No data loss was observed.
Root cause: connection pool exhaustion after a deployment changed the retry interval from 2 seconds to 200 milliseconds.
Corrective actions: restore retry interval; add connection-pool saturation alert; introduce load test gate; document rollback criteria.
Log excerpt: 2026-10-22T09:16:44+05:30 ERROR pool exhausted request_id=test-7f31 route=/parse status=503.

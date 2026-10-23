Production Incident Report

Synthetic document created for document-parsing evaluation.

Incident summary

Incident

Service

Start

Impact

INC-2026-042

Severity

SEV-2

Document Router API

Status

Resolved

09:14 IST

Resolution

11:26 IST

17.4% of synthetic requests received HTTP 503 responses. No data loss was observed.

Timeline

Time

09:14

09:17

10:02

11:26

Root cause

Event

Error rate increased

Alert triggered

Configuration rollback applied

Incident resolved

Connection pool exhaustion occurred after a deployment changed the retry interval from 2 seconds to 200 milliseconds.

Log excerpt

2026-10-22T09:16:44+05:30 ERROR pool exhausted request_id=test-7f31 route=/parse status=503 2026-10-22T09:17:01+05:30 WARN retry scheduled delay_ms=200 attempt=4 2026-10-22T10:02:19+05:30 INFO configuration rollback applied retry_ms=2000 2026-10-22T11:26:08+05:30 INFO incident resolved health=green

Corrective actions

1. Restore retry interval. 2. Add saturation alert. 3. Introduce load-test gate. 4. Document rollback criteria.

Synthetic benchmark document - no real personal or commercial data

Page 1
# Production Incident Report

Synthetic document created for document-parsing evaluation.

# Incident summary

|Incident|INC-2026-042|Severity|SEV-2|
|---|---|---|---|
|Service|Document Router API|Status|Resolved|
|Start|09:14 IST|Resolution|11:26 IST|

# Impact

17.4% of synthetic requests received HTTP 503 responses. No data loss was observed.

# Timeline

|Time|Event|
|---|---|
|09:14|Error rate increased|
|09:17|Alert triggered|
|10:02|Configuration rollback applied|
|11:26|Incident resolved|

# Root cause

Connection pool exhaustion occurred after a deployment changed the retry interval from 2 seconds to 200 milliseconds.

# Log excerpt

2026-10-22T09:16:44+05:30 ERROR pool exhausted request_id=test-7f31 route=/parse status=503 2026-10-22T09:17:01+05:30 WARN retry scheduled delay_ms=200 attempt=4 2026-10-22T10:02:19+05:30 INFO configuration rollback applied retry_ms=2000 2026-10-22T11:26:08+05:30 INFO incident resolved health=green

# Corrective actions

1. Restore retry interval. 2. Add saturation alert. 3. Introduce load-test gate. 4. Document rollback criteria.

Synthetic benchmark document - no real personal or commercial data Page 1
# M4: Guardian, explicit human authorization, simulated application, optional SAM 3.1 request builder

**Scope:** Digital-twin demonstration only. This is **not** an electrical controller, production security system, persistent approval service, or live image segmentation implementation.

## Architecture and risk boundaries

1. M3 provides an energy schedule for the forecast-based planning horizon. Solar values used for planning come from a synthetic previous-day profile; synthetic future observed solar is held out until post-approval evaluation.
2. The M4 Guardian **recomputes** the M3 schedule from the original forecast-time request and policy, then runs the M1 physics again. Altered output, invalid energy accounting, battery-reserve violation or predicted degradation to essential load triggers denial. A warning is emitted for residual essential shortfall or increased flexible-load shortfall. The Guardian cannot guarantee the forecast will be correct or prevent all shortages under unexpected real-world conditions.
3. An explicit human decision (`approved` or `rejected`) is required. Operator identity comes from the trusted local API configuration, not the request body; in the offline CLI it is an explicitly supplied operator label, **not authenticated identification**.
4. Only after approval, before expiry, and by the approving operator can a proposal be applied **to the synthetic M1 digital twin**. Application is rejected if the plan changes after approval, or has already been applied.
5. Events are hash-chained in-process: proposed → approved/rejected → applied/expired. This detects accidental editing of an exported event chain but is **not** durable, signed, replicated or tamper-proof against privileged memory access. Use a persistent append-only event store, robust authentication, CSRF/rate limiting and transaction integrity before any deployment.
6. M4 provides an isolated SAM 3.1 **request builder only** for explicit PNG/JPEG image bytes (max 2 MB) and three whitelisted equipment noun phrases. It does **not** send Meta API requests, return segmentation masks, or diagnose faults. To add actual SAM inference later, use the official `meta_sam_parser` and separately authorize billed network calls. SAM outputs must not authorize electrical control.

## Important deployment restriction

Do **NOT** expose the M4 demo approval HTTP endpoints to the internet or reverse proxy. They are disabled by default and use a single-process in-memory store with static environment operator credentials. A proxy could make external requests appear loopback, so client-address checking is defense in depth only. Start Uvicorn with `--host 127.0.0.1`, one worker, no network forwarding. Do not deploy these endpoints to Cloud Run as currently written.

## Python 3.11/3.12 Windows setup

Apply on top of **M3**, using a fresh branch; do not copy over an M2-modified `api.py` without merging the router additions. From your repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[pipeline,dev]"
python -m pytest -q
python scripts/m4_demo.py --scenario critical_priority_school --operator my-local-demo
```

The CLI prints a proposed forecast-based schedule **before** asking the operator to enter `approved` or `rejected`. If the operator rejects, nothing is applied. To explicitly apply to a synthetic twin:

```powershell
python scripts/m4_demo.py --scenario critical_priority_school --operator my-local-demo --apply-simulation
```

For reproducible automated test scripts only, add `--decision approved`; this is not a substitute for interactive human review.

## Optional authenticated local API demo

**Only on a trusted local workstation, and never with a real Meta API key as the operator token:**

```powershell
$env:M4_ENABLE_LOCAL_API = '1'
$env:M4_OPERATOR_ID = 'local-operator'
# Enter a distinct random operator secret (at least 20 characters); do not put in the repository.
$secret = Read-Host 'Local approval demo bearer token' -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try { $env:M4_OPERATOR_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
python -m uvicorn eden.sentinel.api:app --host 127.0.0.1 --port 8000
```

Send `Authorization: Bearer <your own local token>` to POST `/m4/proposals` with `{"scenario":"critical_priority_school"}`. Retrieve `/m4/proposals/{id}`, POST `/m4/proposals/{id}/decision` with `{"decision":"approved"}` or `{"decision":"rejected"}`. Only after approval POST `/m4/proposals/{id}/execute-simulation`. All endpoints are disabled when `M4_ENABLE_LOCAL_API` is unset. Use the CLI instead of the API if you do not need the local HTTP proof.

## Verification criteria

- Passing legacy M1–M3 and M4 tests on Python 3.11 and 3.12.
- Gate denies unapproved, expired, rejected, repeated, corrupted, altered-policy and unauthorized-operator simulation applications.
- Forecast-time Guardian does not inspect held-out actual solar for approval.
- Essential load priority, reserve constraints and energy accounting remain satisfied in the digital twin.
- Zero Meta billing and zero hardware/cloud I/O during offline tests.
- Operator reviews residual demand trade-offs and explicitly authorizes each simulated application.
- Document real CI run URLs, source SHA, manual smoke checks, rule-eligibility evidence, and remaining security limitations; require owner approval before merging or beginning M5.

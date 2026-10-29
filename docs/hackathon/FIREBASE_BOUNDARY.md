# Inherited Firebase and production boundary

Verified from configuration and source on 2026-10-30; no cloud resources were queried.

- `.firebaserc` selects inherited project `eden-522ce` by default. Treat it as a
  production resource, not a Sentinel sandbox. Its existence, permissions and operational
  state have not been verified.
- `firebase.json` defines Firestore `(default)` in `nam5`, rule/index files, and the
  `functions/` codebase. Functions and Firestore emulator ports are 5001 and 8080.
  There is no RTDB emulator configured here; starting these emulators alone does not
  isolate the inherited RTDB integration.
- `functions/index.js` registers RTDB triggers in `us-central1` with `maxInstances=10`
  and forwards requests to `THINK_URL`, `LEARN_URL`, and `ACT_URL` parameters.
- `eden.core.config` reads environment variables and a local `.env`; inherited RTDB
  uses `FIREBASE_DB_URL` and Application Default Credentials, including
  `GOOGLE_APPLICATION_CREDENTIALS`. Pub/Sub uses the configured project ID (including
  Google project aliases) and the inherited Sense/Think/Learn/Act topic names.
- `EDEN_ENV=dev` is a label, not a production access guard. Valid credentials plus
  inherited service requests can write RTDB and publish messages.

## M0 operating rule

Do not run Firebase deploy commands, inherited job/service endpoints, authenticated
cloud commands, or production reads/writes as part of Sentinel remediation. Do not
mount credentials, pass a cloud environment file, or attach production identities to
Sentinel. Any future cloud access requires explicit owner authorization identifying
the project and allowed resources. No cloud deployment is authorized for M0.

Sentinel exposes only `/health`, imports only its own schemas, and needs no Firebase,
Pub/Sub, ADC, or Meta credentials. `Dockerfile.sentinel` excludes inherited runtime
source and pipeline extras. The existing EDEN Dockerfile and services are preserved.
The full Python suite stubs Firebase/Pub/Sub and blocks external socket connections so accidental
production connections fail. Loopback and local socket pairs remain available for Windows
asyncio internals. Run it from the isolated remediation worktree without a `.env`.
No actual `.env` or `cred.json` is needed or permitted for these checks.

Local container check (requires Docker; image build downloads Python dependencies):

```powershell
docker build -f Dockerfile.sentinel -t sentinel-m0 .
docker run --rm --network none --name sentinel-m0 sentinel-m0
# In a second terminal, loopback access inside the container:
docker exec sentinel-m0 python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/health').read().decode())"
```

This is a local container check, not cloud deployment or proof of inherited services.

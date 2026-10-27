# EDEN — Education, Energy & Nature

Multi-agent platform by RavensAI: **Sense → Think → Learn → Act**, with a Guardian policy gate.
Stages communicate over Pub/Sub and record each episode in Firebase RTDB under
`eden/{communityId}/episodes/{senseId}`.

This repository also contains **EDEN Grid Sentinel**, RavensAI's entry for the Meta Global AI Developer
Hackathon 2026: an AI-assisted solar microgrid operator prototype. Status: **M0 scaffold** — `/health`
endpoint and Pydantic event contracts only. See [docs/hackathon/](docs/hackathon/).

## Layout

```
src/eden/
  core/          config (env / .env), JSON logging
  integrations/  rtdb.py (Firebase init + episode writes), pubsub_io.py
  agents/        sense, think, learn, act, guardian
  services/      FastAPI Pub/Sub push endpoints; pipeline.py holds the shared stage logic
  sentinel/      Grid Sentinel (hackathon-new): api.py, schemas.py
functions/       Firebase Functions (RTDB triggers -> agent URLs)
jobs/sim_job/    Cloud Run job stub
tests/           offline tests (pipeline + tests/sentinel)
docs/            setup guide, hackathon brief, milestones, architecture, provenance
```

## Run locally

Python 3.11 or 3.12. Windows step-by-step: [docs/SETUP_WINDOWS.md](docs/SETUP_WINDOWS.md).

```bash
python -m venv .venv && . .venv/Scripts/activate
pip install -e ".[pipeline,dev]"                   # Sentinel only: ".[dev]"
cp .env.example .env                               # fill in values

pytest -q                                          # offline, no cloud access needed
uvicorn eden.sentinel.api:app --port 8000          # Grid Sentinel /health
uvicorn eden.services.think:app --port 8080        # pipeline stage: think / learn / act
python -m eden.agents.sense                        # simulated sensor stream
```

Credentials come from Application Default Credentials: the attached service account on
Cloud Run, or `GOOGLE_APPLICATION_CREDENTIALS` pointing to a key **outside** the repo locally.

## Deploy the pipeline

One image serves every stage; choose it with `EDEN_SERVICE`:

```bash
gcloud run deploy eden-think --source . --set-env-vars EDEN_SERVICE=think,FIREBASE_DB_URL=...
```

| Service | Endpoint        | Publishes to        |
|---------|-----------------|---------------------|
| think   | `/pubsub/think` | `eden-think-output` |
| learn   | `/pubsub/learn` | `eden-learn-tasks`  |
| act     | `/pubsub/act`   | `eden-act-actions`  |

## Development rules (Grid Sentinel)

- No automatic physical actuation. All energy operations are simulated.
- No API keys or service accounts in commits, logs, screenshots, or documentation.
- No unverifiable model or performance claims; record actual evidence.
- Milestones must be tested, documented, and approved before advancement.
- Keep hackathon code in `src/eden/sentinel/` and record any reuse of pre-existing EDEN code in
  [BASELINE.md](docs/hackathon/BASELINE.md).

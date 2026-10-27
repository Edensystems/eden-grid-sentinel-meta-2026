# Setup — Windows PowerShell

## 1) Python environment

Use Python 3.12, or 3.11 if 3.12 is not installed (3.14+ is not supported yet: no grpc wheels).

```powershell
py -3.12 --version
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[pipeline,dev]"    # Sentinel only: ".[dev]"
Copy-Item .env.example .env                   # fill in; never commit
python -m pytest -q
```

If activation is restricted, run `.\.venv\Scripts\python.exe` instead of `python`. No global execution-policy change is needed.

## 2) Verify the Grid Sentinel API

PowerShell terminal A:

```powershell
python -m uvicorn eden.sentinel.api:app --host 127.0.0.1 --port 8000
```

PowerShell terminal B:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health | ConvertTo-Json
```

Expected JSON fields: `status=ok`, `service=eden-grid-sentinel`, `phase=M0`, `data_mode=simulation`.

## 3) Commit baseline and publish

Install Git and GitHub CLI if missing (`winget install --id GitHub.cli -e`), then from the repository root:

```powershell
gh auth login
gh auth status
git status --short          # confirm no cred.json, .env or .idea
git commit -m "chore: establish EDEN + Grid Sentinel M0 baseline"
gh repo create <owner>/<repo-name> --private --source . --remote origin --push
```

Run only **one** `gh repo create` command.

## 4) Capture evidence for M0 approval

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
gh run list --limit 5
python -m pytest -q
```

Confirm both Python CI matrix jobs succeed. Paste only the repo URL, commit SHA, test output, and CI status into `docs/hackathon/M0_REPORT.md`; never paste tokens or `.env` values.

## M0 exit gate

M0 is *not complete* until the private repository exists, local tests and GitHub Actions are green, the official rules have been reviewed, and the project owner explicitly approves moving to M1.

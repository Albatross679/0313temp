# Audit Pattern Catalog

This file defines patterns for the project-audit skill. To extend for new project types, add a new section following the existing format.

## 1. Gitignore Patterns

Organized by ecosystem. Check which are missing from the project's `.gitignore`.

### Python

| Pattern | Description |
|---------|-------------|
| `__pycache__/` | Bytecode cache directories |
| `*.pyc` | Compiled bytecode files |
| `*.pyo` | Optimized bytecode files |
| `.eggs/` | Egg build artifacts |
| `*.egg-info/` | Egg metadata directories |
| `dist/` | Distribution packages |
| `build/` | Build output |
| `.venv/` | Virtual environment |
| `venv/` | Virtual environment (alt name) |
| `.env` | Environment variables file |
| `.tox/` | Tox test runner cache |
| `.pytest_cache/` | Pytest cache |
| `.mypy_cache/` | Mypy type-checker cache |
| `.ruff_cache/` | Ruff linter cache |
| `htmlcov/` | Coverage HTML reports |
| `coverage.xml` | Coverage XML output |
| `.coverage` | Coverage data file |

### Node.js

| Pattern | Description |
|---------|-------------|
| `node_modules/` | Dependencies |
| `dist/` | Build output |
| `.next/` | Next.js build |
| `.nuxt/` | Nuxt.js build |
| `.output/` | Nitro/Nuxt output |
| `.parcel-cache/` | Parcel bundler cache |
| `.turbo/` | Turborepo cache |

### ML / Data Science

| Pattern | Description |
|---------|-------------|
| `wandb/` | Weights & Biases run data |
| `mlruns/` | MLflow run data |
| `output/` | Training output directory |
| `checkpoints/` | Model checkpoints |
| `*.pt` | PyTorch model files |
| `*.pth` | PyTorch model files (alt) |
| `*.ckpt` | Checkpoint files |
| `*.h5` | HDF5 model/data files |
| `*.safetensors` | SafeTensors model files |
| `model/` | Model weight directories (if large binaries) |

### IDE / Editor

| Pattern | Description |
|---------|-------------|
| `.idea/` | JetBrains IDE |
| `.vscode/settings.json` | VS Code user settings |
| `*.swp` | Vim swap files |
| `*.swo` | Vim swap files (alt) |
| `*~` | Editor backup files |
| `.project` | Eclipse project |
| `.classpath` | Eclipse classpath |

### OS Files

| Pattern | Description |
|---------|-------------|
| `.DS_Store` | macOS directory metadata |
| `Thumbs.db` | Windows thumbnail cache |
| `desktop.ini` | Windows folder settings |
| `*.lnk` | Windows shortcut files |

### Build / Cache

| Pattern | Description |
|---------|-------------|
| `.cache/` | Generic cache directory |
| `target/` | Rust/Maven build output |
| `vendor/` | Go vendored dependencies |

### LaTeX

| Pattern | Description |
|---------|-------------|
| `*.aux` | Auxiliary data |
| `*.log` | Compilation log |
| `*.out` | Hyperref output |
| `*.toc` | Table of contents |
| `*.synctex.gz` | SyncTeX data |
| `*.fls` | File list |
| `*.fdb_latexmk` | Latexmk database |
| `missfont.log` | Missing font log |
| `*.bbl` | Bibliography output |
| `*.blg` | BibTeX log |

## 2. Clutter Patterns (Delete Candidates)

### Temp Files

| Pattern | Description |
|---------|-------------|
| `*.tmp` | Temporary files |
| `*.temp` | Temporary files (alt) |
| `*.bak` | Backup files |
| `*.orig` | Original/merge conflict files |
| `*.swp` | Swap files |
| `temp.*` | Temp-prefixed files |
| `tmp.*` | Tmp-prefixed files |

### Misplaced Archives

Flag `*.zip`, `*.tar.gz`, `*.tar.bz2`, `*.rar`, `*.7z` in the project root (not inside `assets/`, `vendor/`, or `data/` dirs where they may be intentional).

### Empty Files

Flag 0-byte files. Exceptions (do not flag):
- `__init__.py`
- `.gitkeep`
- `.keep`
- `.gitignore` (empty but intentional)

### Duplicate Indicators

Flag files matching these naming patterns:
- `*(1)*`, `*(2)*` -- OS copy suffix
- `*copy*`, `*Copy*` -- Manual copy
- `*-old*`, `*-backup*` -- Manual backup
- `*_bak*` -- Backup suffix

## 3. Stale Patterns (Archive Candidates)

### Stale Documentation

Markdown files (`.md`) outside core project docs not modified in 30+ days, when the project has commits within the last 14 days.

Directories to check: `docs/`, `experiments/`, `issues/`, `logs/`, `knowledge/`, `references/`, `tasks/`.

Exclude from staleness checks: `README.md`, `CHANGELOG.md`, `LICENSE.md`, `CLAUDE.md`, `CONTRIBUTING.md`.

### Stale Logs

Log files (`*.log`) older than 14 days.

### Draft / WIP Files

| Pattern | Description |
|---------|-------------|
| `draft-*` | Draft documents |
| `wip-*` | Work in progress |
| `old-*` | Explicitly marked old |

### Superseded Files

Files matching `*-v1.*`, `*-v2.*`, etc. when a higher version exists in the same directory. Flag the lower versions.

## 4. Large Directory Thresholds

| Level | Threshold | Action |
|-------|-----------|--------|
| Flag | > 100 MB | Include in report, suggest gitignore or cleanup |
| Warn | > 500 MB | Highlight prominently, recommend immediate action |
| Alert | > 1 GB | Top of report, likely needs gitignore + cleanup |

Common large directory offenders:
- `node_modules/` -- Often 500MB+
- `.git/` -- Flag if > 1GB (suggest `git gc` or shallow clone)
- `wandb/` -- ML run logs accumulate quickly
- `model/`, `checkpoints/` -- Model weights
- `data/` -- Dataset directories (verify if intentionally tracked)
- `venv/`, `.venv/` -- Python virtual environments (200MB+)

## 5. Project Type Detection

Detect project type to load the relevant gitignore patterns.

| Indicator File | Project Type |
|---------------|--------------|
| `pyproject.toml` | Python |
| `setup.py` / `setup.cfg` | Python |
| `requirements.txt` / `Pipfile` | Python |
| `package.json` | Node.js |
| `tsconfig.json` | TypeScript |
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `pom.xml` | Java (Maven) |
| `build.gradle` | Java (Gradle) |
| `Gemfile` | Ruby |
| `*.tex` (any) | LaTeX |
| `wandb/` or `train*.py` or `*.pt` | ML project |
| `docker-compose.yml` | Docker |
| `Dockerfile` | Docker |

A project may match multiple types (e.g., Python + ML + LaTeX). Apply all matching pattern sets.

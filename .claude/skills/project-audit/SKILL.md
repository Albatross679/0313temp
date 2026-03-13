---
name: project-audit
description: Audit any project directory for clutter, unused files, uncommitted changes, stale artifacts, and large runtime directories -- then present categorized recommendations the user can selectively execute. Use when the user asks to "organize", "clean up", "audit", "declutter", or "tidy up" a project or directory, or asks about unused files, stale artifacts, what to gitignore, or how to reduce project size.
---

# Project Audit

Scan a project directory, categorize findings, present an actionable report, and execute user-approved cleanup actions.

This skill works for any project directory. Pattern definitions in [references/patterns.md](references/patterns.md) are extensible -- load them during the Scan phase for the full pattern catalog.

## Audit Workflow

### Phase 1: Scan

Gather raw data about the project directory. Run each step and collect results.

1. **Git status** -- Run `git status` to identify modified, deleted, and untracked files. If not a git repo, note this and skip git-related checks.

2. **Runtime/cache directory sizes** -- Run `du -sh` on common runtime and cache directories that exist:
   - `output/`, `wandb/`, `mlruns/`, `checkpoints/`, `model/`
   - `__pycache__/`, `.cache/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
   - `node_modules/`, `dist/`, `build/`, `.next/`, `.nuxt/`
   - `venv/`, `.venv/`, `.tox/`, `htmlcov/`
   - `target/` (Rust), `vendor/` (Go)

3. **Root-level clutter** -- List root-level files and flag potential clutter:
   - Temp files: `*.tmp`, `*.temp`, `*.bak`, `*.orig`, `*.swp`, `temp.*`, `tmp.*`
   - Archives: `*.zip`, `*.tar.gz`, `*.rar` in project root
   - OS files: `.DS_Store`, `Thumbs.db`, `desktop.ini`
   - Compiled artifacts: `*.pyc` outside `__pycache__/`

4. **Gitignore gaps** -- Check `.gitignore` for missing common patterns. Detect the project type (see patterns.md "Project Type Detection") and verify ecosystem-specific patterns are present.

5. **Stale file detection** -- Check documentation directories for stale files. A file is "stale" if not modified in 30+ days AND the project has commits within the last 14 days. Directories to check: `docs/`, `experiments/`, `issues/`, `logs/`, `knowledge/`, `references/`, `tasks/`.

6. **Load pattern catalog** -- Read [references/patterns.md](references/patterns.md) for the full list of patterns organized by category and ecosystem. Cross-reference against scan results.

### Phase 2: Categorize

Group all findings into exactly four action categories.

**Gitignore** -- Items that should be added to `.gitignore`:
- Build artifacts and compiled output
- Runtime directories (caches, virtual environments, node_modules)
- IDE and editor files
- OS-generated files
- Large model weights or dataset directories that should not be tracked

For each item, show the gitignore pattern to add.

**Archive** -- Files to move to an `archive/` folder:
- Stale documentation (not modified in 30+ days, project recently active)
- Old experiment logs and superseded files
- Draft/WIP files that appear abandoned: `draft-*`, `wip-*`, `old-*`
- Versioned files where a newer version exists: `*-v1.*` when `*-v2.*` exists

**Delete** -- Files safe to remove:
- Temp files, backup files, swap files
- Empty files (except `__init__.py`, `.gitkeep`, `.keep`)
- Duplicate indicators: files with `(1)`, `copy`, `-old`, `-backup` in name
- Archives in project root (unless they serve a purpose)
- Compiled artifacts already covered by source

**Commit** -- Meaningful uncommitted changes that should be tracked:
- Modified tracked files with substantive changes
- Untracked documentation or code files that should be version-controlled
- Deleted files that should be committed as deletions

### Phase 3: Report

Present findings as a structured report.

**Summary line:** Total files flagged across all categories, total reclaimable disk space.

**Per-category section format:**

```
## [Category Name] ([N] files, [size])

| File | Size | Reason |
|------|------|--------|
| path/to/file | 1.2 MB | [why flagged] |

Suggested action: [specific command or description]
```

Rules:
- Show all four categories even if empty. For empty categories: "No items found."
- Sort files within each category by size (largest first).
- Show individual file sizes in human-readable format (KB, MB, GB).
- End each category with a concrete "Suggested action" line.

### Phase 4: Execute

After presenting the report, ask the user which categories to act on. Offer options like "Execute all", "Just Gitignore and Delete", "Skip Archive", or individual category selection.

**NEVER auto-execute. Always present the report first, then wait for explicit user approval per category.**

**Gitignore execution:**
- Show the patterns to append to `.gitignore`.
- Show a diff preview of the `.gitignore` changes.
- Append patterns (additive only -- never overwrite existing entries).
- Deduplicate: skip patterns already present.

**Archive execution:**
- Create `archive/` directory if it does not exist.
- For git-tracked files: use `git mv`.
- For untracked files: use `mv`.
- Show the full file list before moving. Wait for confirmation.

**Delete execution:**
- Show the exact file list with sizes.
- For git-tracked files: use `git rm`.
- For untracked files: use `rm`.
- Ask for confirmation before deleting.

**Commit execution:**
- Stage the relevant files with `git add` (individual files, not `-A`).
- Show `git diff --cached --stat` for review.
- Ask the user for a commit message or suggest one based on the changes.
- Create the commit only after user confirms the message.

## Design Notes

- **Project-agnostic**: This skill works for any project directory. Detect project type and adapt patterns accordingly.
- **Stale threshold**: Files not modified in 30+ days when the project has commits within the last 14 days. Adjust threshold based on project activity level.
- **Large directory threshold**: Flag directories over 100MB. Warn at 500MB+.
- **Gitignore priority**: If a file is already in `.gitignore`, lower its priority in Delete recommendations -- it is already excluded from version control.
- **Monorepo caution**: For monorepos or unfamiliar project structures, ask the user about directory purposes before categorizing. Do not assume.
- **Extensible patterns**: Load [references/patterns.md](references/patterns.md) for the full pattern catalog. To support new project types, add a new section to that file.

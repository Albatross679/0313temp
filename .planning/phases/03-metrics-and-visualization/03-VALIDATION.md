---
phase: 3
slug: metrics-and-visualization
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4.4 + shell smoke tests |
| **Config file** | none — smoke tests via grep/test commands |
| **Quick run command** | `grep -c 'XX.XX' report/report.tex` |
| **Full suite command** | `grep -c 'XX.XX' report/report.tex && test -f media/icl_sensitivity.pdf && grep 'icl_sensitivity' report/report.tex` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run `grep -c 'XX.XX' report/report.tex` (count should decrease)
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green (0 XX.XX, plot exists, plot referenced)
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | RPT-04 | smoke | `grep -c 'XX.XX' report/report.tex` returns 0 | ✅ | ⬜ pending |
| 03-01-02 | 01 | 1 | RPT-01,02,03 | manual-only | Submit to Gradescope | N/A | ⬜ pending |
| 03-02-01 | 02 | 1 | VIZ-01 | smoke | `test -f media/icl_sensitivity.pdf` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | VIZ-02 | smoke | `grep 'icl_sensitivity' report/report.tex` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No test framework setup needed — verification is via file existence and grep checks.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Test metrics match Gradescope | RPT-01, RPT-02, RPT-03 | Test ground truth not available locally | Submit prediction files to Gradescope, copy scores into report tables |
| LaTeX compiles without errors | RPT-04, VIZ-02 | Requires LaTeX Workshop compilation | Save report.tex, verify PDF renders correctly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 2s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

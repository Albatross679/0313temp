---
phase: 4
slug: error-analysis
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual validation (no automated tests needed) |
| **Config file** | none |
| **Quick run command** | `python3 script/error_analysis.py` |
| **Full suite command** | Visual inspection of LaTeX table output |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Visual inspection of generated statistics
- **After every plan wave:** Compile LaTeX report and verify table renders correctly
- **Before `/gsd:verify-work`:** Table has minimum 3 error rows with concrete examples and COUNT/TOTAL statistics
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | ANL-01 | manual | `python3 script/error_analysis.py` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | ANL-02 | manual | Compile report, visually inspect table | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `script/error_analysis.py` — analysis script that outputs categorized error statistics
- [ ] Report table filled in `report/report.tex` — the qualitative error analysis table

*Wave 0 creates the analysis script; table fill is part of execution.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Error patterns identified across all 3 parts | ANL-01 | Qualitative analysis requires human judgment | Run `python3 script/error_analysis.py`, verify categories cover all 3 parts |
| Qualitative table filled with examples/stats | ANL-02 | LaTeX rendering requires visual inspection | Compile report, check table has concrete examples and statistics |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

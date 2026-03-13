---
name: repetition-penalty-zero-bug
description: repetition_penalty=0 would cause division by zero in HuggingFace generate
type: issue
status: resolved
severity: high
subtype: model
created: 2026-03-11
updated: 2026-03-11
tags:
  - part2
  - t5-scratch
  - config
  - bug
aliases: []
---

# repetition_penalty=0 Division by Zero Bug

## Context

Config `T5ScratchConfig_restricted_v2` had `repetition_penalty: float = 0`.

## Symptom

Would cause division by zero in HuggingFace `generate()` at runtime, since
the penalty is applied as a divisor to token logits.

## Root Cause

Config value was set to `0` instead of `1.0` (which means "no penalty").

## Fix

Changed to `repetition_penalty: float = 1.0` before launching any runs.

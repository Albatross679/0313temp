# Known Training Issues — Quick Reference

Action-oriented summaries for rapid diagnosis during monitoring. For full details (root causes, prevention, code fixes), see the canonical source: `ml-workflow/references/known-issues.md`.

| Pattern | Symptom | Immediate Action |
|---------|---------|-----------------|
| **Hung process** | Process alive, no log output, W&B shows FINISHED | Outputs saved. `kill <PID>`. Safe. |
| **OOM crash loop (sweeps)** | All trials OOM after one failure | Kill sweep. Check `sweep_train()` exception handling. |
| **Buffered stdout** | Log file empty for long periods | Must restart with `PYTHONUNBUFFERED=1`. |
| **GPU lock contention** | Command hangs at startup, no output | `script/gpu-lock.sh status`. Kill holder if dead. |
| **LoRA state dict mismatch** | `Error(s) in loading state_dict` on resume | Current code uses `merge_and_unload()`. Old checkpoints: apply LoRA first. |
| **MLP device mismatch** | `Expected all tensors to be on the same device` | Call `model = model.to(device)` after wrapping. |
| **Inter-trial OOM fragmentation** | Later trials OOM at smaller batch sizes | Restart sweep process. Agent auto-resumes. |
| **PEFT not installed** | `No module named 'peft'` | `pip install peft`. |
| **SQL EM tokenizer artifact** | SQL EM 0% despite correct-looking SQL | Check post-processing regex normalization. |

# Qwen follow-up execution record

This file records the provider-layer failures that prevented completion of the locked Qwen3-8B follow-up. It is evidence for the dated deviation note in `paper/methods_lock.md`; no partial Qwen follow-up result is used in the paper.

## Original final-upgrade run

- Workflow run: https://github.com/NTinkicht/Research-GridPoisonRAG/actions/runs/37928683708
- Head SHA: `da08733c5aed6a39bd72619d75a1f0ef543a533d`
- Qwen job ID: `113995935046`
- Commit-required control: completed successfully.
- BM25 sensitivity: completed successfully.
- Stage C forced-composition control: failed.
- Result staging/upload: skipped by the old workflow after Stage C failed, so the completed Qwen commit/BM25 runner-local files were not retained.
- Provider evidence in the job log: repeated OpenRouter HTTP 429 responses followed by `404 Not Found` for `https://openrouter.ai/api/v1/chat/completions` at 2026-10-09T16:04:14Z.

The same workflow completed successfully for Mistral Small 3.2 and GPT-5.6 Luna.

## Qwen-only recovery run

- Workflow run: https://github.com/NTinkicht/Research-GridPoisonRAG/actions/runs/37975803086
- Head SHA: `d41ad05b5b4279c4e4f9d06baa50edf1090ad125`
- Qwen recovery job ID: `113973668138`
- The recovery failed during the commit-required stage; downstream BM25, Stage C and finalization jobs were skipped.
- No usable recovery artifact is retained.

## Exploratory backup decision

The Gemini 2.5 Flash-Lite backup workflow was added and triggered only after the original Qwen failure and after the completed Mistral and Luna follow-up results were available. Gemini used the same locked prompts and context definitions plus its own matched B2 baseline. Gemini is exploratory only, is not a member of the locked model family, and does not determine any locked verdict.

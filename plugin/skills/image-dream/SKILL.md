---
name: image-dream
description: Create one imaginative artwork grounded in research, using native Codex subscription image generation; keep detailed provenance private and publish reviewed images, titles and research inspiration to a GitHub Pages gallery. Use for Image Dream runs, migration, validation, and publication.
---

# Image Dream

Use the user's private series configuration. It specifies source access, creative direction, output directories and publication permission. Read it afresh every run. Never infer permission to publish a new user's private source material from this skill.

## Preserve the creative contract

The series configuration controls source choice and artistic direction. Changing runtime or publishing must not change that contract. Read the entire creative history, including migrated works, before selecting a concept. Consider several distinct source-grounded ideas; choose a coherent artwork, which may connect several findings. Avoid overused ideas, metaphors, compositions and palettes. No forced topic alternation or mechanical style rotation. Inspect 1–3 actual reference images, and record their roles. Use real files as native generation references when appropriate; only claim conditioning when they were passed. Landscape 16:9, no visible text unless the user requests otherwise. Show scientific relationships accurately, but transform the material into art rather than a labelled scientific figure.

## Runtime and directories

Use native Codex image generation with the account authenticated for the executing Codex runtime. Do not store account IDs, copy tokens, pin an account, use API keys, or substitute external image providers. `codex login status` checks CLI login mode; it does not prove App and CLI share the same current account or that generation works. A successful native image call is the capability test. On an unavailable tool or denied entitlement, record the exact blocker without retrying through another provider.

The public repository and private directory must be separate sibling directories. Keep source snapshots, detailed hypotheses, full prompts, references, logs, and original files in the private directory. The public repository contains only this workflow and explicitly exported gallery assets. `.gitignore` is a secondary guard.

Resolve all helper paths relative to this SKILL.md. Use `uv run --frozen --project <skill-directory> python <skill-directory>/scripts/dream.py ...` (or the repository's `./dream` wrapper). `scripts/dream_runs.py` is dependency-free and can run with the same Python. Do not modify source repositories or user login settings.

## One occurrence

1. For a scheduled run, compute `dream.py due --timezone <configured-zone>`. Process only this newest due slot. Check the private migration map, run history, and public gallery for the same occurrence before reserving. Test keys must be distinct from nightly keys.
2. Run `dream_runs.py reserve --output <private-directory> --key <key>`. Continue only when `claimed: true`. An existing reservation or interrupted result never authorizes another image call. If a completed image exists but publication failed, resume export/push/deployment only.
3. Freshly read the configured sources and full history. Save `brief.md` and the complete `prompt.md` inside the reserved run directory before generating. Brief: source path/section/revision; findings versus hypotheses; reference files and roles; candidate ideas; selected idea; artistic style, palette, composition and novelty; biological invariants.
4. Call the native image tool **once at most**. Preserve its actual output as `image.png` (or its real original format) inside the run directory. If output download/save fails, record its returned location and a recoverable failure; do not regenerate. A script-generated placeholder is not completion.
5. View the generated pixels. Check meaning, defects, labels/text and whether any unpublished specifics appear. Write `qa.md` with what was actually inspected. Keep an unsuitable image privately; do not automatically retry generation.
6. Finalize with `dream_runs.py finish --output <private-directory> --key <key> --status complete --note <inspection-outcome> --image <run-image> --prompt <run-prompt> --brief <run-brief>`. Use `blocked` or `failed` with an exact cause when appropriate. Completion means the image and provenance exist, not that publication succeeded.

## Public export and publication

Create `public.json` privately, matching `assets/metadata.schema.json`. Public fields are ID, title, date, kind, a concise research-inspiration summary, and public paper links. Unpublished sources may contribute only broad themes; never expose proposal-specific hypotheses, private citations/paths or full prompts. Verify cited papers support the wording. For migrated work, explicitly mark missing dates as null and do not invent provenance. Keep distinct variants; deduplicate identical pixels using a private alias map.

Inspect both the image and public text before running:

```sh
./dream export --repo <public-repo> --image <run-image> --metadata <run-public-json> --reviewed
./dream validate --repo <public-repo>
./dream build --repo <public-repo>
./dream publish --repo <public-repo>
```

`export` decodes pixels, strips embedded metadata, preserves image dimensions and stores one PNG plus strict JSON. `validate` checks schema, hashes, dimensions, duplicates and extra files. These mechanical checks cannot establish scientific validity or privacy; agent review is still required. The fixed template produces all pages. Do not write per-run HTML.

`publish` stages only allowlisted gallery files, commits and pushes the existing main branch without force. It refuses a pre-staged index and holds a local publish lock. Do not use `git add .`, switch branches, rewrite history or stage private data. Publication must be authorized by the series configuration or current user.

Record exported/pushed/deployed status and observed revision in the private run's `publication.json`. GitHub Actions validates and builds the same files, then deploys `_site` only. Check the Actions run, then `./dream verify --url <gallery-url> --revision <pushed-sha>`. A successful push or HTTP 200 alone is not deployment verification. Retry publication safely without another image generation call.

## Scheduling and reporting

Use the host's supported automation tool. Local scheduling requires the host, app and source volume to be available. Keep exactly one active scheduler for a series; migration must disable its predecessor only after the replacement workflow has passed a live test. Do not assume an interactive test proves a scheduled wakeup.

Show each completed image with title, one concise source/artistic interpretation sentence and gallery link. Notify on a new or changed actionable failure. Stay quiet for duplicate/no-due runs and unchanged blockers. Keep complete private records even when a user-facing report is brief.

## Validation and maintenance

Run `uv run --frozen --project plugin/skills/image-dream pytest tests -q` and `./dream build --repo .` from the repository. Review the rendered desktop/mobile gallery after layout changes. Dependencies are pinned in `uv.lock`; update them deliberately. Code is MIT; see the repository README for artwork and research-source scope.

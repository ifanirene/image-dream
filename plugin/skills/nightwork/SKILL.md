---
name: nightwork
description: Encounter personally chosen research through visual art, recent-paper discovery, and reflection. Use for Nightwork setup, one-off or scheduled artworks, source selection, and gallery publication with native Codex image generation.
---

# Nightwork

Use the user's private series configuration. It specifies source access, creative direction, output directories and publication permission. Read it afresh every run. Never infer permission to publish a new user's private source material from this skill.

## Begin with the user's research

For a new series, read [sources and participation](references/sources.md). Let the user point to an existing folder, library collection, or a few selected texts and questions. Discover available connections before asking for setup. Do not require an export or create another authoritative library. A small selection can express the user's interests; do not infer that every item in a large library is equally important. Save source scope and publication choices in the private series configuration. Installation alone does not authorize a schedule or public publishing.

The artwork and short research note invite the user to form associations and discuss them with others. Anchor the note in the source finding without explaining every visual relationship. A surprising or beautiful image is not by itself evidence of a new scientific insight. Do not force a daily discussion question or automatically turn votes into creative restrictions.

## Art direction

The private series configuration sets the user's creative preferences. Preserve them when changing tools or publishing. Use these principles to develop each work:

- **Find an idea worth seeing.** Look for a relationship, tension or question in the research. Consider distinct visual interpretations before choosing one coherent artwork; several findings may contribute. Keep the source connection meaningful without requiring a one-to-one visual code.
- **Let the image stand on its own.** Evocative imagery, curiosity and interpretive space matter. Abstract, playful and dreamlike work are welcome. Allow different moods; do not make every image calm or lyrical. Ground the accompanying research note in evidence and leave viewers room for their own associations.
- **Make style serve the idea.** Choose composition, viewpoint, scale, space, rhythm, light, color and medium together. Possible languages include surreal landscapes, ink painting, ukiyo-e, Art Nouveau, geometric abstraction, cubism, expressionism, watercolor, collage, retrofuturist illustration, cinematic scenes, folk art, etching and color fields. These are possibilities, not a checklist or rotation.
- **Vary the visual thinking.** Read the complete creative history and look beyond surface novelty. Changing the material of the same network or repeating a familiar composition is not enough. Avoid overused metaphors, palettes and spatial arrangements. Biological forms are welcome when they create a meaningful relationship or tension; they need not appear in every work.
- **Use references deliberately.** Inspect 1–3 actual images and name their roles: evidence, subject, composition or artistic inspiration. Scientific figures inform understanding and are not automatic composition templates. Pass real image files to the generator when useful, and claim conditioning only when they were passed.
- **Review the artwork and its explanation.** Inspect the generated pixels for coherence, distracting defects, unwanted text and private details. Consider whether the intended source connection survives the transformation without forcing the image to explain every variable. Keep measured findings distinct from artistic invention. Default to landscape 16:9 without visible text, unless the user requests otherwise.

## Discover source material

Two modes share the same creative workflow: revisit the selected library, or use it as context to discover recent relevant research. The private configuration can select one or allow either; never impose alternation. Use the abstract to screen and, where sufficient, ground a broad concept. Read relevant primary results, figures or methods when the explanation depends on specific mechanisms, limitations or a cross-study connection. Record exactly what was read; do not claim full-text review from metadata. Search PubMed/biomcp and appropriate preprint sources separately, because PubMed includes only some preprints. Deduplicate preprint/published versions and show the date and publication status in the short source note. Consult [source access](references/sources.md) when attaching a folder, Zotero or EndNote.

Follow the series configuration's allowed sources. When discovery is authorized, use the user's wiki or reference library as context rather than a closed topic list; explore recent primary research and meaningful adjacent connections. Do not require every artwork to originate in the private corpus. Search PubMed/biomcp first for biomedical literature, then publisher pages and built-in web search. Verify publication date, article type and the findings actually used; record source scope, limitations and why the work may interest the user. Do not imply a paper is new to the user unless checked. Keep private context out of public queries and captions. There is no fixed quota or rotation between source types.

## Runtime and directories

Use native Codex image generation with the account authenticated for the executing Codex runtime. Do not store account IDs, copy tokens, pin an account, use API keys, or substitute external image providers. `codex login status` checks CLI login mode; it does not prove App and CLI share the same current account or that generation works. A successful native image call is the capability test. On an unavailable tool or denied entitlement, record the exact blocker without retrying through another provider.

Private creation does not require a user repository or public gallery. If publishing is chosen, keep the public repository and private directory separate. Keep source snapshots, detailed hypotheses, full prompts, references, logs, and original files in the private directory. The public repository contains only this workflow and explicitly exported gallery assets. `.gitignore` is a secondary guard.

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

Show each completed image with its title, the linked paper and date/status, a brief account of the core finding and why it may interest the user, plus the gallery link if published. Leave interpretive room; an artistic reading is an invitation, not the single correct explanation. Distinguish the artistic metaphor from the measured result. Notify on a new or changed actionable failure. Stay quiet for duplicate/no-due runs and unchanged blockers. Keep complete private records even when a user-facing report is brief.

## Optional personal feedback

After delivering a completed artwork, offer two optional native in-chat choice questions: **Visual preference: Like / Neutral / Dislike** and **Did it bring an association to mind? Yes / Not yet**. In Codex use `request_user_input_async` when available; include the artwork title and stable run key in both questions. Offer them with delivery, without blocking it or sending reminders for unanswered questions. If the host cannot show choice cards, accept a short numbered reply in chat. No comments, public repo, hosted service or gallery are required.

When an actual answer arrives, save only the answered dimensions using `scripts/feedback.py record --output <private-root> --key <run-key> --response-ref <actual-user-reply-reference>` with `--appeal like|neutral|dislike` and/or `--association yes|not-yet`. Preselection, silence and general enthusiasm are not answers. Keep delayed replies tied to their original work; acknowledge the saved answer without generating again. An explicit withdrawal uses `unanswered`. Read existing run records to resolve the key; do not fabricate completed runs for old images.

The helper writes one current personal response per completed run, preserving separate references for the two answers. `scripts/feedback.py stats --output <private-root>` reports separate counts, unanswered totals and percentages; its denominator is completed local runs, not verified views or people. Responses stay private. These choices do not automatically train a model, dictate a style, or prove a scientific insight. Further feedback-guided creation remains a separate user choice.

## Validation and maintenance

Run `uv run --frozen --project plugin/skills/nightwork python -m pytest tests -q` and `./dream build --repo .` from the repository. Review the rendered desktop/mobile gallery after layout changes. Dependencies are pinned in `uv.lock`; update them deliberately. Code is MIT; see the repository README for artwork and research-source scope.

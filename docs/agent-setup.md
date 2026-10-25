# Set up Nightwork with your agent

This guide is for the agent helping a new user. Start with one private artwork from a small existing source selection. Install, source access, scheduling and public publishing are separate choices.

## Install

Requires Codex with native image generation available to the executing account, Python 3.11–3.13, and [uv](https://docs.astral.sh/uv/). Git/GitHub authentication is needed only for publishing. Use the current runtime's login; no image API key is needed. App and CLI authentication should be checked separately when changing accounts.

```sh
codex plugin marketplace add ifanirene/nightwork --ref main
codex plugin add nightwork@nightwork
```

Or point Codex directly at [the skill](../plugin/skills/nightwork/SKILL.md). Example request:

> Use Nightwork with this PDF folder. Start with one private artwork, and show me the research behind it.

Image Dream users: install Nightwork, check it is available, then remove the old `image-dream@image-dream` plugin entry. Historical run IDs, images, reservations and hashes do not change. The `./dream` CLI remains a compatibility alias for `./nightwork`.

## Connect existing research

Read [source access and participation](../plugin/skills/nightwork/references/sources.md). Prefer an existing connection or a user-selected folder. PDF/Markdown/text folders and EndNote internal PDF attachments can be read in place. Zotero can use the existing connector or its read-only local API. EndNote native groups/notes are not yet parsed. Do not require a new export or maintain a second library.

```sh
./nightwork sources files /existing/research/folder
./nightwork sources files /existing/library.enlp
./nightwork sources zotero --collection COLLECTION_KEY
```

These commands output private metadata, not paper summaries. Inspect the relevant source with the host's reading tools. Use abstracts to screen; read targeted primary sections where the explanation needs more detail. Never infer that finding a file means it was read.

## Save a private series configuration

Start with a private output directory. A public repository is optional; if the user chooses one, keep it separate from private output. A compact `config.md` outside Git should identify:

- Selected source locations and read permissions; any papers/questions the user especially cares about.
- Source mode: revisit the library, discover recent related work, or allow both without forced alternation.
- The user's artistic interests and room for exploration, without turning examples into fixed themes.
- Private run root, optional public repository/gallery, and explicit publication permission.
- Optional schedule and time zone, using the host's supported automation.

Preserve the existing user's creative contract when upgrading. A fresh installation does not inherit the maintainer's private sources, aesthetics or publishing permission.

## Run privately, publish optionally

Follow the skill's occurrence reservation, one native generation call, private prompt/brief persistence, actual visual review and separate publication state. Publication resumes from saved pixels; it never needs a second generation.

Only when publishing is authorized, create the strict [metadata JSON](../plugin/skills/nightwork/assets/metadata.schema.json) privately. Include the title, concise research note, and public source links. Keep private hypotheses and full prompts out of captions and image content.

```sh
./nightwork export --repo . --image /private/run/image.png --metadata /private/run/public.json --reviewed
./nightwork validate --repo .
./nightwork build --repo .
./nightwork publish --repo .
./nightwork verify --url https://OWNER.github.io/REPO/ --revision COMMIT_SHA
```

Enable GitHub Pages with GitHub Actions. Change `site.json` to the owner's repository and gallery URLs. Optional `gallery_title` and `gallery_intro` fields set the gallery's own name and introduction; Nightwork remains the plugin name. These fields are plain text. CI validates/builds/deploys `_site`; it holds no image-generation credentials. The publish command stages gallery records/images only. Review workflow/config changes separately. Local schedules require the computer, app and source storage to be available; keep one scheduler per series and preserve existing occurrence keys.

## Optional choices in chat

After delivering an artwork, offer two optional native choice cards: visual preference (Like / Neutral / Dislike) and whether an association came to mind (Yes / Not yet). Save only the user's actual answers beside the private completed run. The agent handles persistence and can summarize personal statistics; no public repo, comments or hosting setup is needed. See [private feedback](feedback.md) for recording, revisions and interpretation.

## Curation and maintenance

`./nightwork hide --repo . --ids ID ...` changes display only; `show` reverses it. Hidden works stay archived and inform creative-history review. Export strips embedded image metadata; public image bytes and captions share a stable record ID. Original images stay private.

```sh
uv run --frozen --project plugin/skills/nightwork python -m pytest tests -q
./nightwork build --repo .
```

Review desktop/mobile rendering after UI edits and verify the exact deployed revision. A validation pass is not a substitute for source/visual review. Code is MIT; the license does not grant rights in third-party papers or reference images. Do not commit source libraries, unpublished drafts, credentials, feedback exports or internal run logs.

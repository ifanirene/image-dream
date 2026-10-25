# Sources and participation

Read when starting a series, connecting a library, or changing source modes. Use the user's existing selection as the authoritative source; an inventory is a disposable cache, never a library they must maintain separately.

## A small first step

Ask for an existing folder/collection or a few papers and, if helpful, a sentence about what interests the user. They can give selected research, observations, or questions. Reuse a connected source when available. Confirm only access scope and whether output is private or public; do not turn setup into a research questionnaire. On-demand creation works before scheduling or gallery setup.

Keep source settings, inventories, source text, prompts and run history in the private directory. Recheck the selected source every run. A new/deleted/changed file or updated library item must be reflected in the next reading. Do not modify libraries or import duplicates into them. Public discovery queries must use general research terms, not unpublished hypotheses copied from private notes.

## Existing folders and EndNote files

```sh
./nightwork sources files /path/to/existing/papers
./nightwork sources files /path/to/MyLibrary.enl
./nightwork sources files /path/to/MyLibrary.enlp
```

This helper lists paths, formats, sizes and modification times; it does not read paper contents or prove their identity. Use the host's document tools for the selected files. A folder can contain PDF, Markdown and text. Read a small index/selection first rather than ingesting an entire drive.

EndNote `.enl` is accompanied by a same-name `.Data` directory; `.enlp` is a macOS package containing these. The helper reads existing internal `.Data/PDF` attachments in place. It does not parse the native database, groups or notes. Records without PDFs and externally linked attachments are outside this coverage; ask for a known additional folder only if needed. No export is required for attachment access. If the user already has a bibliographic export, it can be used, with its snapshot date recorded. Do not request a new export as the normal onboarding path or treat `.enlx` backups as a live library.

## Zotero

Prefer the host's existing Zotero connector. Otherwise the official local API can read the current library without a cloud API key. Zotero must be running with Advanced → “Allow other applications on this computer to communicate with Zotero” enabled. Use read requests only, without exposing the local port to the network.

```sh
./nightwork sources zotero --collection COLLECTION_KEY
./nightwork sources zotero --item ITEM_KEY
```

The second command returns child notes/attachment metadata for one selected item. The local API's attachment `/file` endpoint can provide an accessible file location. Use the existing connector or documented API to read it; do not assume metadata means the PDF was read. The default inventory cap is 200; a `truncated` result requires paging or a deliberate narrower selection, not a claim of full-library review. Online-only access can use an already authorized connector or dedicated read-only Web API credentials held privately; do not demand another credential when local access works.

## Revisit and discover

**Revisit:** choose meaningful concepts from the user's selected texts and their relationships. Keep the selection personal, without treating repeated authors or keywords as a complete description of the user's interests.

**Discover:** use that selection and expressed questions to find recent relevant primary work in PubMed and appropriate preprint sources such as bioRxiv/medRxiv. Follow promising adjacent connections as well as close topic matches. Verify actual publication/posting dates, source type, available abstract and findings. Collapse preprint/published versions of the same study, retaining version/date and a stable DOI. Label preprints as such. Recency is a preference, not a claim that the user has never seen a paper.

Abstract-first screening reduces setup and reading cost. An abstract can support a broad conceptual artwork and a correspondingly broad research note. Inspect targeted full-text sections when a mechanism, experimental detail, interpretation or connection requires it. If those details cannot be checked, keep the note within the available evidence or choose another candidate. Record `abstract`, `selected full-text sections` (name them), and any inspected figures in the private brief. Do not require comprehensive full-text review or retrieval of the user's entire attachment library for every image.

## The encounter

Pair the artwork with a short note that makes the research accessible: the core finding, why it may relate to the user's interests, source link/date/status. Leave visual interpretation open. Let selecting initial texts, recognizing an association, responding to an image and sharing an interpretation all be forms of participation. Do not make comments or daily homework a condition of using Nightwork.

Anonymous gallery feedback separates visual appeal from inspiration and allows multiple feelings plus optional text. These are viewer responses, not automatic instructions to repeat a style or proof of scientific discovery. Use them for later discussion only within the user's authorized scope. No feedback-driven schedule or automatic taste optimization is enabled by connecting sources.

References: [Zotero Local API](https://www.zotero.org/support/dev/web_api/v3/local_api), [EndNote attachment paths](https://docs.endnote.com/docs/endnote/2025/v1/macos/en/content/03editref/selctngrltvpthabspthforfileatt.htm), [NIH preprints in PubMed](https://pmc.ncbi.nlm.nih.gov/about/nihpreprints/).

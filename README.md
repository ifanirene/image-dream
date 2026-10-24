# Image Dream

[Open the gallery](https://ifanirene.github.io/image-dream/)

Source-grounded conceptual art, generated locally with native Codex image generation and published through a small, reproducible static pipeline. The gallery contains images, titles, research inspiration and public paper links. Detailed research notes, prompts, references and run logs remain outside this repository.

## Use

Requires Codex with native image generation available to its currently authenticated subscription, Python 3.11–3.13, [uv](https://docs.astral.sh/uv/), Git, and GitHub authentication for publishing. No image-generation API key or account ID is stored here. App and CLI login state must be checked separately if you switch accounts; this workflow does not override either.

The portable skill is [plugin/skills/image-dream/SKILL.md](plugin/skills/image-dream/SKILL.md). Read it directly in Codex, or install the lightweight plugin using the included marketplace:

```sh
codex plugin marketplace add ifanirene/image-dream --ref main
codex plugin add image-dream@image-dream
```

Create a private sibling directory for your source settings and runs. Point the skill at your private configuration. Keep source selection and artistic preferences there. The example below describes only public export, after generation and visual review:

```sh
./dream export --repo . --image /path/to/private/run/image.png \
  --metadata /path/to/private/run/public.json --reviewed
./dream validate --repo .
./dream build --repo .
./dream publish --repo .
./dream verify --url https://OWNER.github.io/REPO/ --revision COMMIT_SHA
```

See [the public metadata schema](plugin/skills/image-dream/assets/metadata.schema.json). Each `gallery/works/<id>/` contains exactly `artwork.png` and `record.json`. Export removes embedded image metadata and records the exact file hash and dimensions. Original image bytes are retained privately. Previews are generated without cropping. Captions and images share the same record ID; the webpage is built from these records, never edited by hand.

## Publish and test

Enable GitHub Pages with **GitHub Actions** as the source. Pushes to `main` run tests, validate the entire gallery, build the site and deploy `_site`. The workflow uses pinned action commits and locked Python dependencies. It needs no Codex credentials and performs no image generation.

```sh
uv run --frozen --project plugin/skills/image-dream pytest tests -q
./dream build --repo .
python3 -m http.server 8042 --directory _site
```

The build is deterministic for the same records, code revision and locked environment. An image-generation prompt is a reproducible procedure, not a promise of identical generated pixels. Structural tests do not replace visual inspection or scientific/privacy review.

Local automation requires the computer, Codex and source storage to be available. An occurrence is reserved before generation. A duplicate or interrupted reservation never triggers a blind second image call. Failed push/deployment can resume from the saved image.

## Archive and licensing

Legacy artworks retain their original dimensions and dates where established. Missing information is stated rather than invented. Duplicate file copies are consolidated; distinct artworks remain separate. The private migration ledger preserves original paths, identities, hashes and unresolved recovery work.

The workflow code and documentation are provided under [MIT](LICENSE). Generated art is identified as AI-generated conceptual art; this software license does not grant rights in third-party papers, reference images or other underlying material. Linked papers retain their own licenses.

# Anonymous gallery responses

The gallery supports separate 1–5 visual-appeal and inspiration ratings, multiple feelings, and optional comments. All are optional. Unanswered is `null`, never zero or a negative vote. Responses are saved only on Send; the interface confirms success only after a successful server response. A viewer may change a response or clear and remove it.

The included receiver is a small Cloudflare Worker with D1. GitHub Pages continues to host the gallery. No account is required for viewers. Hosting needs the gallery owner's Cloudflare account; this repo does not activate one or a paid plan.

## Deploy the receiver

From `feedback/`, run `npm ci` using Node 22 or later. Sign in using `npx wrangler login` if needed. Create a D1 database with `npx wrangler d1 create nightwork-feedback`.

Copy `wrangler.jsonc` to ignored `wrangler.deploy.jsonc`. Replace the example database ID with the returned ID. Set `ALLOWED_ORIGIN` to the gallery origin, without a path, and `GALLERY_URL` to the full gallery URL with its repository path. Choose a rate-limit namespace unused by other apps on this account. Keep `observability.enabled` false so the application does not log submissions.

```sh
npx wrangler d1 migrations apply nightwork-feedback --remote --config wrangler.deploy.jsonc
npx wrangler secret put ADMIN_TOKEN --config wrangler.deploy.jsonc
npx wrangler deploy --config wrangler.deploy.jsonc
```

Use a fresh random admin token of at least 32 characters. Store it privately; never put it in `site.json`, browser JavaScript or a shell argument committed to history. `/health` checks that the database is ready. Before enabling the public form, submit a synthetic response for a public work, verify it through the authenticated export, and remove it using the same browser token.

Then set `feedback_url` in the repository's `site.json` to the HTTPS worker origin and deploy Pages. Do not include an admin token, query string or `/feedback` suffix in this URL. The receiver validates artwork IDs against the published site manifest, so new nightly works need no backend redeployment. Changes may take up to one minute to appear in its cache.

## Export and interpret

`GET /admin/export` requires `Authorization: Bearer <ADMIN_TOKEN>`. Read it through a private agent environment; do not paste the token into the gallery or a public URL. The JSON contains up to 500 rows and a `next_offset` for pagination. Save exports outside the public repository. Use `?offset=N` for the next page.

One random browser token maps to one mutable response per artwork. The receiver stores a hash, not the token, and does not request names, accounts, email or location. It stores current answers plus creation/update times; it does not retain every earlier revision. Comments are private to the gallery owner. The browser remembers drafts and selections locally; clearing browser storage loses that editing identity. A different browser can submit again. These are anonymous browser responses, not verified individual people, and they do not automatically distinguish the owner from visitors.

The service applies a per-token rate limit, validates size/fields and restricts browser origins. It does not prevent every form of automated voting. Hosting providers may retain their normal infrastructure logs. Keep raw responses private, separate the two rating distributions, retain unanswered counts, and treat feeling selections as categories rather than a quality score. Do not infer a research insight from a high inspiration rating alone or automatically rewrite creative rules from votes.

## Local review

```sh
npx wrangler d1 migrations apply nightwork-feedback --local
npx wrangler dev --local --port 8787 --var ALLOWED_ORIGIN:http://127.0.0.1:8042 --var GALLERY_URL:http://127.0.0.1:8042/
```

In another terminal, from the repository:

```sh
./nightwork build --repo . --preview-feedback-url http://127.0.0.1:8787
python3 -m http.server 8042 --bind 127.0.0.1 --directory _site
```

This uses local D1 data. Production builds use `site.json` and never inherit the preview override. Keep `.dev.vars`, local database state and deployment config ignored. Tests use an in-memory SQLite adapter to check SQL behavior; local Worker/browser checks exercise the actual receiver separately.

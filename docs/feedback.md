# Private choices in chat

After showing a completed artwork, offer two optional choices in the same chat:

- **Visual preference:** Like / Neutral / Dislike.
- **Did it bring an association to mind?** Yes / Not yet.

Use the host's native choice cards when available. In Codex, `request_user_input_async` can show both questions without blocking delivery. Put the artwork title and stable run key in each question so a delayed reply stays attached to the right work. A preselected choice is not an answer. If native cards are unavailable, offer a short numbered reply in chat; do not ask the user to configure a form or server. No comment, GitHub account, public repo or gallery is required.

Only save actual user answers. Map “Like / Neutral / Dislike” to `like / neutral / dislike`, and “Yes / Not yet” to `yes / not-yet`. Leave skipped questions unanswered. On a later reply, save it for the original artwork and acknowledge briefly; do not generate another artwork just because feedback arrived. If the intended artwork or answer is ambiguous, ask rather than infer it from general praise.

## Save an answer

The helper uses the same private root and stable occurrence key as `dream_runs.py`. It writes `feedback.json` beside the completed run. The agent runs these commands, not the user:

```sh
./nightwork feedback record --output /private/series --key NIGHTLY_KEY \
  --appeal like --association not-yet --response-ref USER_REPLY_REFERENCE
./nightwork feedback stats --output /private/series
```

For an installed skill, run `python <skill>/scripts/feedback.py` directly; it needs only the Python standard library. `--response-ref` is a private message reference or a dated description of the actual reply. Each dimension keeps its own reference. Either choice can be saved alone; a later update preserves the other one. To withdraw a choice, explicitly set that dimension to `unanswered`. Repeated replies replace the current choice for that work rather than adding votes.

The helper rejects missing or unfinished runs. Statistics cover completed local runs under this private root; imported images without native run records are not included. Do not create fictional completed runs to expand that denominator. Completed runs are not proof that the user viewed each image.

## Read the statistics

Each question reports its own answer counts, unanswered count, and percentages among answers. No answers gives a null percentage, not zero approval. These are one person's choices across artworks, not a population survey. Keep the file and statistics private unless the user asks to share them.

A positive association answer means an association came to mind, not that a scientific idea was validated. A visual preference does not identify the liked feature. The helper collects choices and summarizes them; it does not train a model or automatically rewrite the user's creative rules. Discuss any later use of these responses to steer creation separately.

The old hosted form has been removed. Feedback does not depend on Cloudflare, public Issues, browser storage, or gallery publication. Private files remain on the user's computer; chat replies use the current chat service.

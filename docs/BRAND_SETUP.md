# Brand setup (do this once, before your first edit)

ForwrdCut ships brand-neutral. Everything that makes an edit look and sound like *your*
brand lives in a few files you fill in. None of them are committed (they're git-ignored),
so your brand assets and claims stay on your machine.

## 1. Project config: `config.toml`

```toml
[brand]
name = "yourbrand"             # your brand/channel name
niche = "your niche"           # e.g. "outdoor gear", "skincare"; grounds trend research
platforms = ["tiktok", "reels", "shorts"]

[captions]
highlight = "#EA6024"          # your accent color for emphasised caption words

[library]
expected_terms = ["yourbrand", "your product"]   # helps `forwrdcut audit` flag junk clips
```

## 2. Brand kit: `brands/<yourbrand>.toml`

```bash
cp brands/example.toml brands/yourbrand.toml
```

Fill in:

| Section | What to put there |
|---|---|
| `[brand]` | On-screen name and URL |
| `[style]` | Accent hex; paths to your logo PNGs |
| `[voice]` | Banned words, em-dash policy |
| `[claims].approved` | Every stat, rating, offer, warranty or spec your ads may state, worded exactly as you're allowed to say it. Pull these from your live product page, review platform and policies. |

Then reference it in any EDP with `"brand": "yourbrand"` and check copy with:

```bash
forwrdcut lint --plan path/to/plan.edp.json
```

Seasonal offers (sales, holiday returns) belong in `[claims]` too. Remove them when they
expire so old ads can't be re-rendered with stale terms.

## 3. Assets

- `assets/brand/`: your logos (e.g. `logo_white.png`, `logo_dark.png`, transparent PNG).
- `assets/fonts/`: optional brand fonts. Point an overlay's `"font"` at one, or set
  `[captions] font` in `config.toml`. Inter is bundled as the default.
- `assets/music/licensed/`: music you're licensed to use. It's never committed, because
  your license lets you *use* it, not redistribute it. Procedural beds in `assets/music/`
  are the royalty-free fallback.

## 4. Pronunciation and spelling (optional)

- **VO pronunciation:** add brand or product words the TTS mispronounces to `_LEXICON` in
  `src/forwrdcut/audio/tts.py` (regex → respelling).
- **Caption spelling:** Whisper may mishear your brand name. Map misheard forms to the
  correct on-screen spelling in `_BRAND_CAPTION` in `src/forwrdcut/render/timeline.py`.

## 5. Tell the agent

If you drive ForwrdCut with Claude Code, give it your product page URL and brand kit name
in the first message (e.g. *"make a Meta ad for yourbrand.com/products/x, brand kit
`yourbrand`"*). `AGENTS.md` tells the agent to use only claims from your kit.

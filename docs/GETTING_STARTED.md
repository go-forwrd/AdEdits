# Getting started (for first-timers)

This guide takes you from nothing to your first finished, on-brand video. No video-editing
experience needed. Budget about 30 minutes for setup the first time.

**What ForwrdCut is:** a video editor you run from the terminal, designed to be driven by an
AI agent (Claude Code). You give it footage and tell it what you want ("make a 15-second
Meta ad for this product"); it finds the best shots, writes and voices a script, cuts the
edit, adds captions, music and your branding, then checks its own work.

**What you need:**
- A Mac (Apple Silicon is fastest) or Linux. Windows works via WSL, but isn't tested.
- About 2 GB of free disk space, plus room for your footage.
- Some footage of your product: phone videos, b-roll, customer UGC, or photos.
- Optional but recommended: [Claude Code](https://claude.com/claude-code), so you can edit by
  just describing what you want.

---

## Part 1: Install (one time)

### 1. Install the prerequisites

On a Mac, open **Terminal** and install [Homebrew](https://brew.sh) if you don't have it,
then:

```bash
brew install python@3.12 ffmpeg git
```

On Linux (Ubuntu/Debian):

```bash
sudo apt update && sudo apt install -y python3.12 python3.12-venv ffmpeg git
```

> Use Python **3.12** specifically. Some video libraries may not have installers for newer
> versions yet, which makes `pip install` fail.

### 2. Download ForwrdCut

```bash
cd ~                       # or wherever you keep projects
git clone https://github.com/go-forwrd/AdEdits.git
cd AdEdits
```

Every command from here on is run **inside this `AdEdits` folder**.

### 3. Create a Python environment and install

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[voice]"
```

`source .venv/bin/activate` turns the environment on for your current Terminal window. Your
prompt will show `(.venv)`. **Run it again every time you open a new Terminal window**
before using ForwrdCut.

### 4. Download the voiceover model (recommended)

ForwrdCut voices scripts with Kokoro, a free neural voice that runs on your computer:

```bash
mkdir -p models/kokoro
curl -L -o models/kokoro/kokoro-v1.0.onnx \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -L -o models/kokoro/voices-v1.0.bin \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

Skip this and voiceovers fall back to the built-in macOS voice (or ElevenLabs, if you set
`ELEVENLABS_API_KEY`). The speech-to-text model downloads itself the first time it's needed.

### 5. Check everything works

```bash
forwrdcut doctor
```

It prints a checklist. Fix anything marked ✗ (it tells you how). Warnings (⚠) about brand
kits and licensed music are expected until you do Part 2.

Then render the built-in demo to prove the pipeline works end to end:

```bash
python examples/quickstart_ad.py
open renders/quickstart_9x16.mp4          # Linux: xdg-open
```

You should see a short vertical ad with callouts and music. Setup is done.

---

## Part 2: Make it your brand (one time, about 15 minutes)

Nothing in ForwrdCut is pre-branded. These files tell it who you are. They're all
**git-ignored**, so your brand info never gets uploaded if you contribute back.

### 1. Basic project settings: `config.toml`

Open `config.toml` in any text editor and change:

```toml
[brand]
name = "acme"                         # your brand, lowercase, no spaces
niche = "reusable water bottles"      # what you sell; grounds trend research
platforms = ["tiktok", "reels", "shorts"]

[captions]
highlight = "#1E90FF"                 # your brand accent color (hex)

[library]
expected_terms = ["acme", "bottle"]   # words your footage should mention
```

### 2. Your brand kit: `brands/<yourbrand>.toml`

```bash
cp brands/example.toml brands/acme.toml
```

Open `brands/acme.toml` and fill it in:

- **`[brand]`**: your name exactly as it should appear on screen, and your website.
- **`[style]`**: your accent color, and paths to your logo files (step 3).
- **`[voice]`**: words you never want in your ads (e.g. "cheap", "best").
- **`[claims] approved`**: **the most important part.** List every fact your ads are allowed
  to say, worded exactly as you're allowed to say it: star rating, review count, warranty,
  shipping offer, materials, specs. Copy them from your product page and policies.

  ```toml
  approved = [
    "4.8 stars",
    "2,000+ verified reviews",
    "lifetime warranty",
    "free shipping over $40",
    "keeps drinks cold for 24 hours",
  ]
  ```

  Any number or claim in a script that **isn't** on this list gets flagged before render.
  That's what stops an AI from inventing "10,000 happy customers." Keep it current: remove
  sale terms when the sale ends.

### 3. Logos and fonts

```bash
mkdir -p assets/brand
```

Put your logo in `assets/brand/` as transparent PNGs, ideally a white version (for dark
video) and a dark version, e.g. `assets/brand/logo_white.png`. Then uncomment the
`logo_white` / `logo_dark` lines in your brand kit.

Brand fonts (`.ttf`/`.otf`) can go in `assets/fonts/`. The bundled default is Inter.

### 4. Music (optional)

Drop music you have a license for (Epidemic, Artlist, Pixabay, etc.) into
`assets/music/licensed/`. ForwrdCut detects each track's tempo and mood automatically.
Without any, it generates royalty-free background music for you.

### 5. Pronunciation fixes (optional)

If the voiceover mispronounces your brand name, add a respelling to `_LEXICON` in
`src/forwrdcut/audio/tts.py`, e.g. `r"\bacme\b": "ack-me"`. If captions misspell it, add
the fix to `_BRAND_CAPTION` in `src/forwrdcut/render/timeline.py`, e.g.
`{"akmi": "Acme"}`.

Run `forwrdcut doctor` again: it should now list your brand kit.

More detail: [`BRAND_SETUP.md`](BRAND_SETUP.md).

---

## Part 3: Make videos

### Add your footage

```bash
mkdir -p media/source
```

Copy your clips and photos into `media/source/`. ForwrdCut **never modifies** these files;
every output goes to `renders/`. Then index them:

```bash
forwrdcut scan
```

### Option A: Just ask Claude Code (easiest)

From the `AdEdits` folder:

```bash
claude
```

Then describe what you want in plain English. Good first prompts:

- *"Make a 15-second Meta ad for acme.com/products/bottle using my footage. Brand kit `acme`."*
- *"Cut three different TikToks from my clips, each with a different hook."*
- *"Make a YouTube Shorts version and a 4:5 feed version of that last ad."*

Claude reads [`AGENTS.md`](../AGENTS.md) (the editing playbook) and runs the whole loop:
research → pick shots → script + voiceover → edit → render → check. Watch the result in
`renders/`, then give feedback like you would to a human editor ("the hook is slow",
"swap the second shot", "louder music").

Optional: let Claude call the engine directly as tools (faster, more precise):

```bash
claude mcp add forwrdcut -- "$(pwd)/.venv/bin/forwrdcut-mcp"
```

### Option B: Run commands yourself

| You want | Command |
|---|---|
| A finished short from one raw clip | `forwrdcut short --clip media/source/clip.mp4 --platform tiktok` |
| Several shorts from your best clips | `forwrdcut batch --n 3 --platform reels` |
| A feature showcase with headlines | `forwrdcut template --name feature_showcase --clips a.mp4 b.mp4 c.mp4 --headline "MEET *ACME*" --headline "*COLD* FOR 24H" --headline "SHOP *NOW*"` |
| A photo slideshow | `forwrdcut template --name photo_slideshow --clips photos/*.jpg --aspect 9x16` |
| Find a specific moment | `forwrdcut find --q "she pours water into the bottle"` |
| Best practices for a platform | `forwrdcut brief --platform meta_ad` (`--list` shows all) |
| Check a finished video | `forwrdcut qc --file renders/your_video.mp4` |
| Check ad copy against your claims | `forwrdcut lint --plan renders/your_video.mp4.edp.json --brand acme` |

`*word*` in a headline marks the word to highlight in your accent color. Add `--help` to any
command to see all its options.

Every render also saves a `.edp.json` file next to the video (e.g. `your_video.mp4.edp.json`): the full edit as editable
text. Change a caption or timing in it and re-render with
`forwrdcut render-plan renders/your_video.mp4.edp.json`; only the changed parts re-render.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `forwrdcut: command not found` | Run `source .venv/bin/activate` in the `AdEdits` folder first. |
| `config.toml not found` | You're in the wrong folder. `cd` into `AdEdits`. |
| `pip install` fails building opencv/numpy | You're on the wrong Python. Delete `.venv` and redo step 3 with `python3.12`. |
| `ffmpeg not on PATH` | `brew install ffmpeg` (Mac) or `sudo apt install ffmpeg` (Linux). |
| Robotic or wrong voice | Download the Kokoro model (Part 1, step 4). |
| Lint says a claim isn't approved | Either add the true fact to `[claims] approved`, or change the script. Don't approve things that aren't true. |
| First transcription is slow | It's downloading the speech model once (~500 MB). Later runs are cached. |

Still stuck? Run `forwrdcut doctor` and share its output when you ask for help.

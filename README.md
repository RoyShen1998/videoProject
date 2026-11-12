# Meeting Video Summarization Pipeline

Automatically transcribes meeting videos, generates AI summaries, and manages files with auto-cleanup.

## How It Works

```
newVideo/ → extract audio → transcribe (GPU) → summarize (Claude) → save & organize
```

1. Drop a video into `newVideo/`
2. Audio is extracted via ffmpeg and transcribed locally using faster-whisper on your GPU
3. The transcript is sent to Claude (via Claude Code CLI) for summarization
4. A transcript, summary, and renamed video are saved with a descriptive name
5. Processed videos older than 30 days are automatically deleted

## Output

| Folder | Contents |
|---|---|
| `textTranscript/` | Full transcripts (`.txt`) |
| `summary/` | Meeting summaries with key topics, decisions, and action items (`.md`) |
| `processedVideo/` | Renamed original videos (auto-deleted after 30 days) |

All files share a descriptive name like `2026-03-24_quarterly-budget-review.txt`.

## Prerequisites

- **Python 3.10+**
- **ffmpeg** installed and on PATH
- **NVIDIA GPU** with CUDA (used for local transcription)
- **Claude Code** CLI installed and authenticated (`claude` on PATH)

## Setup

```bash
python -m venv .venv
.venv\Scripts\pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu126
.venv\Scripts\pip install -r requirements.txt
```

### Speaker labels (optional)

Transcripts can label who is speaking (`Speaker 1`, `Speaker 2`, ...) using the pyannote diarization model, which runs locally but is gated on Hugging Face. One-time setup:

1. Create a free account at https://huggingface.co
2. Open https://huggingface.co/pyannote/speaker-diarization-community-1 and accept the terms
3. Create a **Read** token at https://huggingface.co/settings/tokens
4. Run `.venv\Scripts\hf auth login` and paste the token

Until this is done (or with `ENABLE_DIARIZATION = False` in `config.py`), transcripts are saved without speaker labels.

## Usage

```bash
python main.py
```

The app watches `newVideo/` for new video files (`.mp4`, `.mkv`, `.webm`, `.avi`), processes them automatically, and keeps running until you press `Ctrl+C`.

Any videos already in `newVideo/` when the app starts are processed immediately.

## Auto-Start at Boot (Optional)

Register as a Windows scheduled task that runs at logon:

```bash
python install_service.py
```

Remove it with:

```bash
python install_service.py --uninstall
```

Requires admin privileges.

## Configuration

Edit `config.py` to change:

- **Whisper model** — default `large-v3` (options: `tiny`, `base`, `small`, `medium`, `large-v3`)
- **Vocabulary** — product names and jargon (`VOCABULARY`) that Whisper and the summarizer should spell correctly
- **Speaker labels** — `ENABLE_DIARIZATION`
- **Summary model** — `CLAUDE_MODEL`
- **Video extensions** — default `.mp4`, `.mkv`, `.webm`, `.avi`
- **Cleanup age** — default 30 days

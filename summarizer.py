import subprocess
import logging

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """\
You are an expert meeting summarizer. Given a transcript, produce:

1. **Title**: A short descriptive title for the meeting (max 8 words, suitable for a filename).
2. **Summary**: A concise meeting summary in markdown with these sections:
   - **Overview** (1-2 sentences)
   - **Key Topics Discussed**
   - **Decisions Made**
   - **Action Items** (with owners if mentioned)

Respond in EXACTLY this format:

TITLE: <your title here>

SUMMARY:
<your markdown summary here>

Here is the transcript:

{transcript}
"""


def summarize(transcript: str) -> tuple[str, str]:
    """Send transcript to Claude CLI and return (title, summary_markdown)."""
    prompt = PROMPT_TEMPLATE.format(transcript=transcript)

    logger.info("Sending transcript to Claude CLI for summarization (%d chars)...", len(transcript))
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI failed: {result.stderr}")

    response_text = result.stdout.strip()
    title, summary = _parse_response(response_text)
    logger.info("Got summary with title: '%s'", title)
    return title, summary


def _parse_response(text: str) -> tuple[str, str]:
    """Parse the TITLE: / SUMMARY: response format."""
    title = "meeting"
    summary = text

    if "TITLE:" in text and "SUMMARY:" in text:
        title_part, summary_part = text.split("SUMMARY:", 1)
        title = title_part.replace("TITLE:", "").strip()
        summary = summary_part.strip()

    return title, summary

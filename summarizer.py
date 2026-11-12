import subprocess
import logging

import config

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """\
Below is an automatic transcript of a work meeting. Write a summary for someone who \
was not in the meeting and needs to know what was discussed, what was decided, and \
what they or others now have to do.

About the transcript:
- It was produced by speech recognition, so some words are mis-heard, especially \
product names and technical terms. Terms this team uses often: {glossary}. When a \
phrase is clearly a garbled version of one of these (or of another term that the \
context makes obvious), use the correct term.
- Speakers may be labelled "Speaker 1", "Speaker 2" and so on. These labels come from \
voice matching and are occasionally wrong. Where the conversation makes a speaker's \
real name clear (someone addresses them by name, or they introduce themselves), use \
the name. Otherwise keep the label rather than guessing.

The summary is markdown with these sections:
- **Overview**: one or two sentences.
- **Key Topics Discussed**
- **Decisions Made**
- **Action Items**: one per line, with the owner and any deadline that was mentioned. \
Say when the owner is unclear instead of assigning one.
- **Open Questions**: anything raised but left unresolved. Omit the section if there \
are none.

Stick to what was said: include ticket numbers, dates and figures as stated, and leave \
out anything you would have to invent. Keep it concise: one line per point, and no \
commentary on the quality of the recording or transcript.

Also give the meeting a short descriptive title (at most 8 words) that works as a \
filename.

Respond in exactly this format, with nothing before TITLE:

TITLE: <title>

SUMMARY:
<markdown summary>

Here is the transcript:

{transcript}
"""


def summarize(transcript: str) -> tuple[str, str]:
    """Send transcript to Claude CLI and return (title, summary_markdown)."""
    prompt = PROMPT_TEMPLATE.format(
        transcript=transcript,
        glossary=", ".join(config.VOCABULARY) or "(none listed)",
    )

    logger.info("Sending transcript to Claude CLI for summarization (%d chars, model=%s)...", len(transcript), config.CLAUDE_MODEL)
    result = subprocess.run(
        ["claude", "-p", "--model", config.CLAUDE_MODEL],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=600,
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

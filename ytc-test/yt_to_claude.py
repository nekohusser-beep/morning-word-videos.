#!/usr/bin/env python3
"""YouTube -> Claude summarizer. One run = one check. Exits early (zero API cost) when nothing is new."""
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import anthropic
import requests
from youtube_transcript_api import CouldNotRetrieveTranscript, YouTubeTranscriptApi

CHANNEL_ID = os.environ["YT_CHANNEL_ID"]                       # e.g. UCaKI8Xsi-MHu78UnJTY1xpg
STATE = Path(os.getenv("STATE_FILE", "last_video.txt"))         # last processed (or given-up) video ID
TRIES = Path(os.getenv("TRIES_FILE", "tries.txt"))              # "VIDEOID:count" for caption retries
OUT_DIR = Path(os.getenv("OUT_DIR", "summaries"))
MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")           # smallest model = lowest cost
MAX_CHARS = int(os.getenv("MAX_TRANSCRIPT_CHARS", "60000"))     # hard cap on input (about 15k tokens)
MAX_OUT = int(os.getenv("MAX_OUTPUT_TOKENS", "350"))            # hard cap on output
MAX_TRIES = int(os.getenv("MAX_TRIES", "6"))                    # caption retries before giving up (free, no API call)
MIN_CHARS = 200
LANGS = [x.strip() for x in os.getenv("TRANSCRIPT_LANGS", "en").split(",")]

SYSTEM = (
    "Summarize the transcript. Output ONLY raw, dense bullet points, one '- ' per line, max 8. "
    "No greeting, intro, filler, headings, commentary or conclusion. Facts, steps and numbers only."
)

ATOM = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


def latest_video_id():
    """Newest upload from the channel's public RSS feed (free, no API key, no quota)."""
    r = requests.get(
        f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}", timeout=20
    )
    r.raise_for_status()
    el = ET.fromstring(r.content).find("a:entry/yt:videoId", ATOM)
    return el.text.strip() if el is not None and el.text else None


def get_transcript(video_id):
    """Transcript text only: no title, description or metadata. Raises on any failure."""
    kwargs = {}
    proxy = os.getenv("YT_PROXY")  # optional, only if YouTube blocks the runner's IP
    if proxy:
        from youtube_transcript_api.proxies import GenericProxyConfig

        kwargs["proxy_config"] = GenericProxyConfig(http_url=proxy, https_url=proxy)
    fetched = YouTubeTranscriptApi(**kwargs).fetch(video_id, languages=LANGS)
    text = " ".join(s.text for s in fetched)
    text = re.sub(r"\[[^\]]{1,30}\]", " ", text)  # [Music], [Applause]
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > MAX_CHARS:  # keep the opening and the ending, drop the middle
        head = MAX_CHARS * 2 // 3
        text = text[:head] + " ... " + text[-(MAX_CHARS - head):]
    return text


def bump_tries(video_id):
    n = 0
    try:
        v, _, c = TRIES.read_text().strip().partition(":")
        if v == video_id and c.isdigit():
            n = int(c)
    except OSError:
        pass
    n += 1
    TRIES.write_text(f"{video_id}:{n}")
    return n


def main():
    try:
        vid = latest_video_id()
    except Exception as e:
        print(f"feed error, nothing sent: {e}")
        return 0
    if not vid:
        print("no videos found")
        return 0

    # 1) State check first: same ID means exit with no transcript fetch and no Claude call.
    if STATE.exists() and STATE.read_text().strip() == vid:
        print(f"no new video ({vid})")
        return 0

    # 2) Transcript, failing gracefully. No transcript means no API call.
    text, why = None, ""
    try:
        text = get_transcript(vid)
        if len(text) < MIN_CHARS:
            text, why = None, "transcript too short"
    except CouldNotRetrieveTranscript as e:
        why = f"no captions available ({type(e).__name__})"
    except Exception as e:
        why = f"transcript error ({type(e).__name__}: {e})"
    if text is None:
        n = bump_tries(vid)
        print(f"{vid}: {why}. Claude not called. Try {n}/{MAX_TRIES}.")
        if n >= MAX_TRIES:
            STATE.write_text(vid)
            print(f"{vid}: giving up, marked as processed.")
        return 0

    # 3) One small Claude call: transcript only, strict system prompt, capped output.
    try:
        msg = anthropic.Anthropic(max_retries=1, timeout=60).messages.create(
            model=MODEL,
            max_tokens=MAX_OUT,
            system=SYSTEM,
            messages=[{"role": "user", "content": text}],
        )
    except anthropic.APIError as e:
        print(f"Claude API error, will retry next run: {e}")
        return 1
    out = "".join(b.text for b in msg.content if b.type == "text").strip()
    print(f"tokens in={msg.usage.input_tokens} out={msg.usage.output_tokens}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{vid}.md").write_text(f"https://youtu.be/{vid}\n\n{out}\n", encoding="utf-8")
    STATE.write_text(vid)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

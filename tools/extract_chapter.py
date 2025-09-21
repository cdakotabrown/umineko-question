#!/usr/bin/env python3
"""Extract structured chapter data from the Umineko Question patch script.

This helper reads the massive ``0.utf`` scenario file, slices out the
requested chapter (identified by a label such as ``*umi1_opning``) and emits a
JSON file that is easier to post-process into EPUB-ready XHTML.

Only the English strings (``langen``) are retained.  Japanese lines, voice clip
annotations, and other control codes are stripped so that the output focuses on
narration, dialogue, and music cues.

Example
-------
To generate the JSON for the first episode's opening, run::

    python tools/extract_chapter.py \
        --config tools/chapter_plan.json \
        --chapter episode1-opening \
        --output-dir build/epub

The resulting ``episode1-opening.json`` can then be converted into the desired
EPUB markup.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

SCRIPT_PATH_DEFAULT = Path("InDevelopment/ManualUpdates/0.utf")

VOICE_TAG_PATTERN = re.compile(r":(?:dwave_eng|dwave_jp|voicedelay|dwave) [^:]*:")
CONTROL_CODE_PATTERN = re.compile(r"!\w+")
WHITESPACE_RUN_PATTERN = re.compile(r"[ \t]{2,}")


@dataclass
class SpeakerInfo:
    """Metadata about a character that might speak in the script."""

    speaker_id: str
    name: Optional[str]
    portrait: Optional[str]

    @classmethod
    def from_dict(cls, speaker_id: str, data: Dict[str, str]) -> "SpeakerInfo":
        return cls(speaker_id=speaker_id, name=data.get("name"), portrait=data.get("portrait"))


@dataclass
class ChapterPlan:
    """Configuration for a single chapter export."""

    chapter_id: str
    title: str
    episode: str
    start_label: str
    end_label: str

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ChapterPlan":
        return cls(
            chapter_id=data["id"],
            title=data["title"],
            episode=data["episode"],
            start_label=data["start_label"],
            end_label=data["end_label"],
        )


def load_plan(config_path: Path) -> tuple[List[ChapterPlan], Dict[str, SpeakerInfo]]:
    """Read the JSON configuration file that enumerates chapters and speakers."""

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    chapters = [ChapterPlan.from_dict(item) for item in payload.get("chapters", [])]
    speakers = {
        speaker_id: SpeakerInfo.from_dict(speaker_id, info)
        for speaker_id, info in payload.get("speakers", {}).items()
    }
    return chapters, speakers


def find_chapter(plan: Iterable[ChapterPlan], key: str) -> ChapterPlan:
    """Return the chapter whose ``id`` or ``start_label`` matches ``key``."""

    for chapter in plan:
        if chapter.chapter_id == key or chapter.start_label == key:
            return chapter
    available = ", ".join(ch.chapter_id for ch in plan)
    raise KeyError(f"Unknown chapter '{key}'. Available ids: {available}")


def index_labels(script_lines: List[str]) -> Dict[str, int]:
    """Create a mapping from label names (``*label``) to their line index."""

    result: Dict[str, int] = {}
    for index, raw_line in enumerate(script_lines):
        stripped = raw_line.strip()
        if stripped.startswith("*") and len(stripped) > 1:
            label = stripped[1:]
            result[label] = index
    return result


def clean_lang_line(raw: str) -> str:
    """Strip control codes and extract the English sentence from a ``langen`` line."""

    content = raw.strip()
    if not content.startswith("langen"):
        return ""

    content = content[len("langen") :]
    content = VOICE_TAG_PATTERN.sub("", content)
    content = content.lstrip(": ")

    # Remove leading caret (if any) so we can process text tokens.
    if content.startswith("^"):
        content = content[1:]

    # Replace control characters with whitespace or nothing, depending on role.
    content = content.replace("^", "")
    content = content.replace("@/", "\n")
    content = content.replace("@", "\n")
    content = content.replace("\\", "")

    # Remove inline scripting hints like !sd or !w800.
    content = CONTROL_CODE_PATTERN.sub("", content)

    # Normalise quotes that are escaped for the engine.
    content = content.replace("\\\"", '"').replace("\"", '"')

    # Condense stray whitespace.
    content = WHITESPACE_RUN_PATTERN.sub(" ", content)
    content = re.sub(r"^\s*:\s*", "", content, flags=re.MULTILINE)
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Drop leftover control characters (keep newlines intact).
    content = "".join(ch for ch in content if ch == "\n" or ord(ch) >= 32)

    return content.strip()


def extract_entries(
    lines: List[str],
    speaker_map: Dict[str, SpeakerInfo],
    music_commands: Optional[Iterable[str]] = None,
) -> List[Dict[str, object]]:
    """Convert raw scenario lines into structured narration/dialogue entries."""

    entries: List[Dict[str, object]] = []
    current_speaker: Optional[str] = None
    music_keywords = {cmd.lower() for cmd in (music_commands or [])}

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith(";"):
            # Comments include speaker hints such as ``;＜金蔵``; keep for debugging if needed.
            continue
        if stripped.startswith("advchar"):
            match = re.search(r'"([^"]+)"', stripped)
            if match:
                speaker_code = match.group(1)
                current_speaker = None if speaker_code == "-1" else speaker_code
            continue

        keyword = stripped.split(" ", 1)[0].lower()
        if keyword in music_keywords:
            entries.append({
                "type": "music",
                "command": keyword,
                "raw": stripped,
            })
            continue

        if stripped.startswith("langen"):
            text = clean_lang_line(stripped)
            if not text:
                continue
            entry: Dict[str, object] = {
                "type": "dialogue" if current_speaker else "narration",
                "text": text,
            }
            if current_speaker:
                entry["speaker_id"] = current_speaker
                speaker_info = speaker_map.get(current_speaker)
                if speaker_info and speaker_info.name:
                    entry["speaker"] = speaker_info.name
                if speaker_info and speaker_info.portrait:
                    entry["portrait"] = speaker_info.portrait
            entries.append(entry)
            continue

    return entries


def slice_chapter(
    script_lines: List[str],
    label_indices: Dict[str, int],
    chapter: ChapterPlan,
) -> List[str]:
    """Return the portion of the script that belongs to ``chapter``."""

    try:
        start = label_indices[chapter.start_label]
    except KeyError as exc:  # pragma: no cover - defensive guard for missing labels
        raise KeyError(f"Start label '*{chapter.start_label}' not found in script") from exc

    try:
        end = label_indices[chapter.end_label]
    except KeyError as exc:  # pragma: no cover - defensive guard for missing labels
        raise KeyError(f"End label '*{chapter.end_label}' not found in script") from exc

    if start >= end:
        raise ValueError(
            f"Chapter '{chapter.chapter_id}' has start label after end label: {chapter.start_label} >= {chapter.end_label}"
        )

    return script_lines[start + 1 : end]


def write_output(
    output_dir: Path,
    chapter: ChapterPlan,
    entries: List[Dict[str, object]],
    speaker_map: Dict[str, SpeakerInfo],
) -> Path:
    """Serialise the extracted data to a JSON file and return its path."""

    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{chapter.chapter_id}.json"

    # Capture only the speakers that are actually referenced in the entries.
    used_speakers = {
        speaker_id: speaker_map[speaker_id].__dict__
        for speaker_id in {entry.get("speaker_id") for entry in entries if entry.get("speaker_id")}
    }

    payload = {
        "chapter": {
            "id": chapter.chapter_id,
            "title": chapter.title,
            "episode": chapter.episode,
            "start_label": chapter.start_label,
            "end_label": chapter.end_label,
        },
        "entries": entries,
        "speakers": used_speakers,
    }

    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract a single chapter from the Umineko script into JSON.")
    parser.add_argument("--config", type=Path, default=Path("tools/chapter_plan.json"), help="Path to the chapter plan JSON file.")
    parser.add_argument("--chapter", required=True, help="Chapter id (or start_label) to export.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory where JSON exports should be written.")
    parser.add_argument(
        "--script-path",
        type=Path,
        default=SCRIPT_PATH_DEFAULT,
        help="Location of the 0.utf master scenario file.",
    )
    parser.add_argument(
        "--music-commands",
        nargs="*",
        default=["bgm", "bgmplay", "bgmstop", "meplay", "meplay2", "bgmfade"],
        help="Additional script commands that should be preserved as music cues.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    script_path = args.script_path
    if not script_path.exists():
        raise SystemExit(f"Script file not found: {script_path}")

    chapters, speakers = load_plan(args.config)
    chapter = find_chapter(chapters, args.chapter)

    script_lines = script_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    label_indices = index_labels(script_lines)
    segment = slice_chapter(script_lines, label_indices, chapter)

    entries = extract_entries(segment, speakers, music_commands=args.music_commands)

    destination = write_output(args.output_dir, chapter, entries, speakers)
    try:
        rel_path = destination.relative_to(Path.cwd())
    except ValueError:
        rel_path = destination
    print(f"Wrote {rel_path}")


if __name__ == "__main__":
    main()

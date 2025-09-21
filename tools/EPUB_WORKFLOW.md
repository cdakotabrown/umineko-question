# EPUB export workflow (chapter-by-chapter)

The upstream script file (`InDevelopment/ManualUpdates/0.utf`) contains the full
scenario for the Question arcs.  To keep commits manageable, extract each
chapter separately with the helper script committed alongside these notes.

## 1. Configure the chapters you want to export

1. Open [`tools/chapter_plan.json`](./chapter_plan.json).
2. Each entry in the `chapters` array points at a label inside `0.utf`.
   * `start_label` is the line that begins the chapter (without the leading `*`).
   * `end_label` is the next label where this chapter should stop.  The helper
     script excludes this label from the export.
   * `id` becomes the output filename (`{id}.json`).
   * `title` and `episode` are written into the JSON metadata for later EPUB
     generation.
3. Extend the `speakers` object with any new character IDs you encounter.
   * The keys correspond to the `advchar` numeric identifiers in the script.
   * `portrait` should point at the square thumbnail you plan to embed later
     (placeholders are fine for now).

At present the plan only contains the Episode 1 opening (`*umi1_opning` →
`*umi1_1`).  When you are ready to work on the next chapter, add another object
with the appropriate `start_label`/`end_label` pair and a new `id`.

## 2. Run the extractor for a single chapter

```bash
python tools/extract_chapter.py \
  --config tools/chapter_plan.json \
  --chapter episode1-opening \
  --output-dir build/epub
```

* Replace `episode1-opening` with the desired chapter ID.
* The output directory (`build/epub` above) can be any location outside the
  repository if you prefer to avoid large diffs.
* Only the English (`langen`) lines are kept.  Voice tags are stripped, but the
  script preserves basic music cues (`bgm*`, `meplay*` by default).  Pass a
  custom `--music-commands` list if you want to keep additional stage
  directions.

The resulting JSON structure contains:

* `chapter`: metadata (title, episode name, script labels).
* `entries`: narration, dialogue (with optional `speaker`, `portrait`), and
  music cues (`type: "music"`).
* `speakers`: only the characters actually referenced in the exported entries.

## 3. Converting the JSON into EPUB-ready markup

This repository intentionally does **not** contain the EPUB assembly step.  Once
all required chapters are exported, you can feed the JSON into whatever tooling
fits your pipeline (e.g. a Jinja2 HTML renderer followed by `pandoc`, or a
custom Python script that emits XHTML spine files and packaging metadata).

Keep the generated EPUB assets (images, XHTML, `content.opf`, etc.) outside of
this Git repository to avoid huge commits—only the automation belongs here.

## 4. Incremental expansion checklist

When preparing the next batch of chapters:

1. Duplicate an existing `chapters` entry in `chapter_plan.json` and update the
   metadata/labels.
2. Add any missing speaker IDs (check for `advchar` values that are not in the
   `speakers` object yet) so that dialogue lines include their names/portrait
   placeholders.
3. Re-run `extract_chapter.py` for the new chapter and inspect the JSON output.
4. Repeat until the entire episode (or the whole Question arcs) has been
   exported.

## 5. Troubleshooting notes

* The parser currently strips engine control codes such as `^`, `@`, `!sd`, and
  the embedded `dwave`/`voicedelay` tags.  If you find formatting artefacts in
  the JSON, adjust `clean_lang_line` in `tools/extract_chapter.py`.
* Add more entries to the `--music-commands` list (either via the JSON config or
  the CLI flag) if you want to retain additional cues such as sound effects.
* `extract_chapter.py` reads the entire `0.utf` file in memory once per run.
  This is fine for chapter-by-chapter exports, but consider caching the label
  index if you automate large batches later.


# [>> CLICK HERE TO INSTALL THE MOD <<](http://07th-mod.com/wiki/Umineko/Umineko-Getting-started/)

<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>


# Developer Information

## Important information

Generally, you only want to look at the main umineko script, on the master branch.

The main umineko script file for development is located in `InDevelopment\ManualUpdates\0.utf`

## Generating EPUB chapter exports

The repository now includes a lightweight extraction script that turns the
massive `0.utf` scenario file into chapter-sized JSON dumps that are ready for
your EPUB tooling.  The example below walks through exporting the Episode 1
opening and producing a very simple EPUB that you can open on an e-reader.

1. **Prepare Python.** Any recent Python 3 (3.9+) works.  Optionally create a
   virtual environment to keep things tidy:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. **Run the chapter extractor.** The helper reads the configuration in
   `tools/chapter_plan.json` and slices `0.utf` between the configured labels.
   This repository ships with the Episode 1 opening configured out of the box:

   ```bash
   python tools/extract_chapter.py \
     --config tools/chapter_plan.json \
     --chapter episode1-opening \
     --output-dir build/epub
   ```

   The command above creates `build/epub/episode1-opening.json`.  Tweak the
   `--chapter` argument (or extend `chapter_plan.json`) when you are ready to
   export more sections of the script.  The JSON bundle contains the prose,
   dialogue metadata, and the speaker roster required for EPUB assembly.

### Prompt template for automated chapter exports

When you queue additional Codex jobs to generate JSON dumps, you can reuse the
prompt below.  Replace the placeholders with the Episode and Chapter you would
like to export; the helper will extend `tools/chapter_plan.json` if necessary
and then run the extractor to write the chapter bundle under `build/epub/`.

```
You are working in the 07th-Mod/umineko-question repository.  Generate a chapter
JSON export for the visual novel "Umineko no Naku Koro ni" using the existing
`tools/extract_chapter.py` helper.  The Episode is: <EPISODE NAME/NUMBER>.  The
Chapter is: <CHAPTER TITLE>.  Ensure the chapter is defined in
`tools/chapter_plan.json` (add or adjust the entry if missing) and then run:

python tools/extract_chapter.py \
  --config tools/chapter_plan.json \
  --chapter <SLUG-FOR-EPISODE-AND-CHAPTER> \
  --output-dir build/epub

Report the path of the resulting JSON file when you are finished.
```

3. **(Optional) Convert the JSON to Markdown.** While the extractor stops at a
   JSON document, the snippet below generates a quick Markdown rendering that
   tools such as `pandoc` understand.  Feel free to adapt it to your preferred
   pipeline:

   ```bash
   python - <<'PY'
   import json
   from pathlib import Path

   payload = json.loads(Path('build/epub/episode1-opening.json').read_text(encoding='utf-8'))
   md_path = Path('build/epub/episode1-opening.md')

   with md_path.open('w', encoding='utf-8') as handle:
       chapter = payload['chapter']
       handle.write(f"# {chapter['title']}\n\n")
       handle.write(f"_From {chapter['episode']}_\n\n")

       for entry in payload['entries']:
           entry_type = entry['type']

           if entry_type == 'narration':
               text = entry.get('text', '').strip()
               if text:
                   handle.write(text + "\n\n")
           elif entry_type == 'dialogue':
               speaker = entry.get('speaker') or payload['speakers'].get(entry.get('speaker_id', ''), {}).get('name', 'Unknown speaker')
               text = entry.get('text', '').strip()
               if text:
                   handle.write(f"**{speaker}:** {text}\n\n")
           elif entry_type == 'music':
               raw = entry.get('raw') or entry.get('command')
               if raw:
                   handle.write(f"*Music cue: {raw}*\n\n")

   print(f"Wrote {md_path}")
   PY
   ```

4. **Produce the EPUB container.** Any EPUB authoring stack works here.  As one
   concrete option, `pandoc` can turn the Markdown into a fully valid EPUB file
   (install it from https://pandoc.org/installing.html if you do not have it):

   ```bash
   pandoc build/epub/episode1-opening.md \
     --metadata title="Episode 1 – Opening" \
     --metadata author="07th-Mod team" \
     -o build/epub/episode1-opening.epub
   ```

   You can now sideload `build/epub/episode1-opening.epub` onto an e-reader or
   open it with any desktop EPUB viewer.  Update the metadata or apply your own
   styling as you iterate on the layout.

See [`tools/EPUB_WORKFLOW.md`](tools/EPUB_WORKFLOW.md) for more context about
maintaining the chapter plan and extending the export list.

## Folder structure:

- `InDevelopment\ManualUpdates\0.utf`: The main umineko script file, where development happens
- `InDevelopment\UminekoVoiceParser`: The c# project which was initially used to merge the voice lines from the old script to the new script
- `dev`: This folder contains the (I believe) original script files. Usually you don't use this folder unless you need to check something
- `image_resizing`: This folder contains xnConvert scripts which can be used to resize PS3 backgrounds etc.
- `tools\VoicePuter`: Contains a c# project which was used to port the japanese voices for the question and answer arcs.
- `tools\adv_mod`: Contains an abandoned c# project which was used to add ADV mode - however please don't use that as reference, the final ADV mode was NOT implemented using this project.
- `umihook`: Contains a project which was used to hook file accesses of the game and play back the PS3 .at3 files externally (as the game doesn't support .at3 files). It would probably be easier to either capture the output from debug mode or recompile the game if you really want to attempt this. The audio quality probably wouldn't be improved significantly even with this method.
- `widescreen`: contains old python scripts used for converting widescreen (consider removal of this folder). The answer arcs repository has more up-to-date scripts.
- `POnscripter_Video_Encode_Settings.txt`: Contains ffmpeg settings used for encoding the videos - however you may still need to play around with the settings and test within the game to make sure they work.

## Asset Backup

Some large files are saved as attachments to release v0.0.0: https://github.com/07th-mod/umineko-question/releases/tag/0.0.0 . These files used to be stored using Git LFS, but we have since stopped usage of Git LFS.

# Umineko no Naku Koro ni (Question Arcs) 

This patch aims to modify the newest release of Umineko by MangaGamer, changing its assets to replicate the PS3 version of the game.
It is compatible with the Steam version ***and*** the MangaGamer DRM-free download. See the roadmap below for current patch status.

## Install Instructions

See the Getting Started guide: http://07th-mod.com/wiki/Umineko/Umineko-Getting-started/

## Troubleshooting

See the [Troubleshooting](http://07th-mod.com/wiki/Umineko/Umineko-Part-0-TroubleShooting-and-FAQ/) section of the Wiki.

## Feedback and bug reports

We now have a discord server: https://discord.gg/acSbBtD . If you have a formal issue to report, please still raise a github issue as it helps us keep track of issues. For small problems/questions however you can just ask on discord.

The patch is now fully released, however some bugs may remain. If you think you've found a bug, first check if the bug has already been reported.

For most issues, it is extremely useful to get the game's error log. Newer auto-installations can simply double click the "Umineko1to4_DebugMode.bat" file to start the game in debug mode. However, if you are missing the batch file, ([download this to your game directory, and rename it as a .bat file](https://github.com/07th-mod/resources/raw/master/umineko-question/utilities/StartUminekoInDebugMode.bat))

Once you have started the game in debug mode, just play until the game crashes or behaves badly, then submit the `stderr.txt` and `stdout.txt` to us (when game is started in debug mode, a folder will appear showing `stderr.txt` and `stdout.txt`).

Open a new issue (or find the relevant existing issue) and please include as much information as you can in the ['Issues'](https://github.com/07th-mod/umineko-question/issues) section. You can copy and paste the following template:

- [a description of the issue]
- [pictures of the issue (if applicable)]
- The bug occurs just after [text from when bug occurs] is shown on the screen
- My operating system is [Windows, MacOS, Linux]
- I installed the game [X Months ago]
- I am running the [Full Patch / Voice only patch]
- I installed the game [Manually / using the Automatic Installer]
- My computer is a [Gaming Beast / Laptop with Integrated Graphics]
- Add the `stderr.txt` and `stdout.txt` to the post

If you're not sure if it's a bug, you can report it on our discord (but try not to post any spoilers, if possible).
We really appreciate your help!

## Screenshots

![](https://i.imgur.com/EWITCxL.jpg)
![](https://i.imgur.com/NXUNU4r.jpg)

## Roadmap

The patch is currently **FINISHED**, although some bugs may remain...

- [x] Voices
- [x] Sprites
- [x] Backgrounds
- [x] Effects
- [x] CGs
- [x] Menus

## Credits

 * [DoctorDiablo](https://github.com/DoctorDiablo)
 * [drojf](https://github.com/drojf)
 * [Forteissimo](https://github.com/Forteissimo)
 * [ReitoKanzaki](https://github.com/ReitoKanzaki)

There is another 'Umineko Modification' project which has a different set of goals, see [Umineko Project](https://umineko-project.org/en/) if you are interested in that.

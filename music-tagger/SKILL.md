---
name: music-tagger
description: Batch update media file metadata (tags) using ffmpeg. Use when needing to update artist, album, or other ID3 tags for multiple files.
version: 2.0.0
kind: pipeline
triggers:
  - "update media tags"
  - "batch tag songs"
  - "update artist metadata"
intent: media
guardrails:
  - Always use `-c copy` so ffmpeg never re-encodes the audio.
  - Write to a temp file and replace on success — never edit in place.
  - Confirm the mapping with the user before running it across a directory.
resources:
  - <SKILL_PATH>/scripts/batch-tagger.py
tools:
  - ffmpeg
  - python3
created_at: 2026-05-30
updated_at: 2026-07-29
---

# Music tagger

Batch-updates media metadata (.m4a, .mp3) via ffmpeg.

## Workflow

1. **Identify** the files and the correct metadata.
2. **Write a mapping** JSON — keys are filenames, values are a tag dict or a bare
   artist string:

   ```json
   {
     "song1.m4a": {"artist": "Artist Name", "album": "Album Name"},
     "song2.m4a": "Artist Name"
   }
   ```

3. **Run it:**

   ```bash
   python3 "<SKILL_PATH>/scripts/batch-tagger.py" /path/to/media mapping.json
   ```

4. **Report** the result lines. On failure, decide whether to retry, fix the
   mapping, or ask the user — the script reports, it does not decide.

## Output

stdout is one tab-separated line per file, stderr carries progress and the count.
Exit `0` all updated, `1` some failed, `2` could not run.

```
updated	song1.m4a	artist=Artist Name,album=Album Name
failed	song2.m4a	Invalid data found when processing input
missing	song3.m4a	no such file
```

Only failing lines need relaying in detail; the file itself is the handle for
anything further.

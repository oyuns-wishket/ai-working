# Portable film manifest

See [film.example.json](../assets/film.example.json). Copy it into the actual production project and fill it with verified local assets/content. Paths are relative to the manifest, or explicit local absolute paths in a **private/project-local** manifest. Never publish personal paths, customer content or provider URLs to this SSOT.

- `title`, `panel_heading`, `fps` (24), `audio_lead` (.25 seconds) and `font` apply to the film. `font.path` is a Korean-capable font, with `regular_index`/`bold_index` for a collection; Apple SD Gothic Neo uses4/6 in the tested Mac environment. Other fonts need their own real indices. Do not assume arbitrary TTFs have Korean glyphs.
- `scenes[]`: `title`, `chapter`, total `frames`, local `audio`, `cuts[]`, `captions[]`, optional `panels[]`, `props[]`, `status`, `footnote`.
- `cuts[]`: local `video`, `source_in` seconds, integer `frames`, `speed:1`, `reviewed:true`, `action`, `meaning`, `icon`. Order is timeline order; total cut frames must exactly equal scene frames. `reviewed` is a human/agent visual review record, never a substitute for inspecting. Record detailed review notes in the project.
- Icons: `box`, `shop`, `supplier`, `bank`, `company`, `receipt`, `contract`, `ledger`, `calendar`, `tv`, `online`, `phone`, `coin`, `truck`, `calculator`, `lock`, `check`.
- `captions[]`: `start`/`end` seconds relative to the original narration audio, `text`. Renderer adds `audio_lead` once. If converting old JSONL 1e7-tick timing, divide by1e7; do not pre-add the delay a second time.
- `panels[]`: `start`/`end` **scene** seconds, `text`, optional `size` (32), `y` (550), `color`. Replace before/after equations through consecutive intervals. Default panel content ends before the status/footer area; use y/size deliberately. Formula strings must be independently checked against source rules and arithmetic.
- `props[]`: `start`/`end` **scene** seconds, `xy:[x,y]`, `text`, optional `to:[x,y]`, `arrive`, `size`, `color`. Coordinates refer to the final1920×1080 canvas. Use these for labels following the actual observed object path. They label existing props; they do not prove the cat moved them.
- `status` keeps a concise current/planned warning visible; `footnote` can identify an illustrative example.

Convert observed source completion to local event time:

```text
event_scene_time = sum(previous_cut_frames)/24 + completion_source_time - source_in
```

Select a cut containing completion; do not clamp an out-of-range event to fake a finished action. This manifest deliberately has no loops, speed-ratio, paid tools or media URLs. For large/complex equations, adapt local graphic primitives while preserving validated timing and readable spacing.

Commands (use the project Python environment; no new dependencies if already available):

```sh
python SKILL/scripts/profile.py inspect LOCAL_PROFILE
python SKILL/scripts/render.py PROJECT/film.json --validate
python SKILL/scripts/review.py PROJECT/action.mp4 PROJECT/action-review.jpg
python SKILL/scripts/render.py PROJECT/film.json --out PROJECT/render-v2 --scene 0
python SKILL/scripts/render.py PROJECT/film.json --out PROJECT/render-v2 --scene 1
python SKILL/scripts/render.py PROJECT/film.json --out PROJECT/render-v2 --finalize
python SKILL/scripts/verify.py PROJECT/film.json PROJECT/render-v2
```

Omit `--scene` to render/finalize all. Existing scene/final video files are not overwritten. An interrupted partial file must be inspected and renamed aside before retrying that local render. Do not use an unrelated generation retry to repair a local render failure.

## Original-film reproduction versus a new film

An existing renderer may import older project modules, timing files and audio assets. Keep its dependency inventory in the local profile's `dependency_manifest`: `{root, files:[{path,sha256}]}` with paths relative to that project root. `profile.py inspect PROFILE --dependencies` verifies the whole inventory without copying customer facts into this public skill. Preserve that project to reproduce the old film. Do not copy just the renderer file and assume it is standalone.

For a new film, use this portable renderer/manifest and the approved reference/voice/benchmark; reuse matching existing clips only after semantic review. This avoids hidden old-project imports. There is no claim that re-generating new dialogue with the same adjectives reproduces the exact speaker identity.

Each rendered scene writes a receipt binding its manifest, source media, font and renderer code hashes. Finalization/verification rejects stale scenes after changes. Render a representative scene into a separate preview output directory, or continue with only the remaining `--scene` indices and then `--finalize`; an all-scenes invocation does not overwrite/skip an existing scene automatically.

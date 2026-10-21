# Editing and final checks

## Environment and composition

Inspect the existing renderer/lockfiles first. The portable compositor needs FFmpeg/ffprobe and Pillow. Stereo verification also uses NumPy/SciPy. Install only missing dependencies in the existing project environment; no global package churn. Confirm a real Korean font by rendering Korean sample glyphs.

The accepted baseline uses a1920×1080 canvas at24fps, warm cream/green palette, a1480×832 complete video stage at(20,124), a compact right-side meaning/calculation panel, and bottom captions. Preserve both paws and the entire prop path. Overlay labels can follow props; do not obscure contact points. Avoid long text lists, overfilled panels and captions spilling off screen. Preview a representative difficult sequence before the whole film.

Decode clips at1×, trim source intervals and concatenate distinct actions. `fps=24` can resample frames without changing duration; do not use narration/source-duration `setpts`, freeze padding, reverse or looping to fill narration. If the action itself is slow/idle, select a more useful source-in/out or another honest action.

Keep narration timing independent from visual generations. The audio filter baseline:

```text
adelay=250:all=1,apad,loudnorm=I=-17:TP=-1.5:LRA=9
```

The historical defect was `adelay=250` on stereo: it delayed only the first channel, producing a second copy/echo250ms apart. Always check actual final stereo alignment. Do not compensate by regenerating a liked voice or pitch-shifting it.

## Repair-only route

When the user asks to remove an echo or duplicate speech while keeping the voice, use the existing clean narration and diagnose the final mix. Do not require a reference image, create shots or restart voice auditions. `profile.py inspect PROFILE --require voice_sample` checks only the voice requirement while reporting other assets.

Compare the final L/R lag against the clean source; the known250ms defect is one hypothesis, not every repetition's cause. Inspect doubled timeline clips or repeated source dialogue if both channels already align. Rebuild the scene audio from **clean source narration**, map the existing video stream with `-map 0:v:0 -map 1:a:0 -c:v copy`, and apply the correct all-channel delay once. Never add250ms to an already delayed final mix. Preserve exact scene duration and rebuild concatenation/chapters if needed. Keep old output and verify final audio, subtitles and duration.

독립 AAC 장면을 stream-copy로 이어 붙이면 encoder padding이 누적될 수 있다. 제공 렌더러는 장면 audio를 정확한 video duration으로 PCM 정렬한 뒤 최종 AAC 트랙 하나로 인코딩한다. 최종 audio를 장면 연결본과 대조해 누적 밀림을 검출한다.

## Narration alignment

Reuse accepted audio when content is unchanged. For new content, generate a bounded chapter at a time and retain source audio. Obtain timestamps through actual tool output or a local aligner/ASR; the prior workflow used local `mlx-whisper` on Apple hardware. Choose an installed suitable aligner elsewhere, not a mandatory extra service.

Do not provide the complete expected script as the ASR `initial_prompt`: it can hallucinate repetitions. Compare an unprompted transcription to the script, inspect spoken transitions, then split chapter audio at actual timestamps. Keep JSONL offsets/units explicit. Text match does not catch stereo echoes, shrillness, noise, malformed syllables or wrong speaker style; inspect/listen to final audio when playback is available.

## Acceptance matrix

1. **Identity/style:** compare reference, first frames and final film; same face/fur/clothing/body and approved soft visual tone.
2. **Actions:** contact sheets/playback show a real before→transfer→after. Verify selected cut includes completion and excludes undo/morph tails. A prompt or task-success status is insufficient.
3. **Meaning:** exact menus/formulas are grounded in this project's current evidence. Label grouped quantities and metaphors; planned APIs remain planned. No false real payment/production completion.
4. **Time:** contiguous integer frame counts, source intervals valid,1× speed, caption delay added once, no truncated voice or repeated filler.
5. **Audio:** whole decode; per-channel delay against the full clean source, with confidence and silence handling; final concatenated video-frame identity and audio correspondence; loudness/true peak. The supplied verifier compares each channel to its own source, preserving intentional stereo differences; it exits2 when silence/periodicity prevents confident alignment. Report silent/low-confidence correlation samples as unverified, not a pass. Use `ffmpeg -i FILM -af ebur128=peak=true -vn -f null -` for loudness.
6. **Visuals:** actual assembled frames across all cuts, Korean glyphs, all numbers visible, no overlapping panel/status/footnote text, no graphics covering paws. Detailed equations may require smaller text or staged states.
7. **Delivery:** MP4, SRT, chapters, manifest/code, actual generation accounting and limitations. Verify HTTP200 and byte-range206 if sharing a review page. Browser playback and user listening are distinct from decode/frame checks; never claim the former without doing them.

Keep a project-local rejected-shot list and an accepted trim list. The reusable lesson is to validate actual action semantics before spending on an entire film, not to memorize one project's scenes or always generate a fixed number of shots.

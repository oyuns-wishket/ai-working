---
name: character-explainer-video
description: Create or revise character-led educational videos where an existing mascot physically demonstrates a business or learning process. Reuse approved character and voice profiles, generate short Runway action shots, and locally composite accurate Korean narration, calculations and captions. Use for the kitten explainer workflow or similar animated instruction, not static slides or ChatGPT pets.
---

# Character explainer video

Make the character **do the thing being explained**. Preserve the approved reference, voice and production method; do not substitute nodding beside a list of text for a demonstrated process. This is an offline edited film workflow, not an application deployment.

## Recover the baseline first

Read the current project instructions, Git status and relevant handoff/production files. Preserve existing code, renders and uncommitted work. Resolve the requested character through `~/.config/ai-working/character-video/profiles/<profile>.json` (or the explicit project profile). The local profile can point to the reference image, voice audition, benchmark film, renderer and production notes. For full baseline reuse run `scripts/profile.py inspect PROFILE --require reference_image --require voice_sample --require benchmark_video --require renderer --require dependency_manifest --dependencies` to verify the requested assets and the original renderer dependency inventory. For a narrower repair require only its needed assets. Missing/changed items are not a valid same-quality baseline; recover them before dependent work. Reuse verified assets, not an expired provider URL.

The established kitten profile name is `mint-kitten`. For it, read [the identity and voice recipe](references/identity-voice.md). Locate the original image before generating new visual assets. If it is missing, search the registered source project and existing attachments; request only the missing original if still unavailable. Do not invent a substitute kitten. Reuse an approved voice rather than restarting auditions. The profile grants **no new paid-generation authorization**.

For a new character or materially new visual direction, resolve the user's reference and preferences first; use the applicable design workflow. A correction within the accepted character/style does not require another style-selection round. Existing user permissions remain valid for their scope.

For an audio-only echo/timing repair, follow the repair-only route in [editing](references/editing.md) first. It needs the clean narration and existing video, not a new reference image, audition or generation.

## Plan what the character physically demonstrates

Read [storyboarding and motion review](references/action-direction.md). Extract facts from current code, screens and source materials; record each menu/formula and its evidence in the project. Do not inherit another project's business rules from a style sample.

For each narration beat specify: **before state → one observable action → after state → meaning → exact local label/calculation → observed completion time**. Prefer moving a single prop, grouping, comparing, opening evidence or filing a document. Exact counts and Korean text belong in local graphics. Use explicitly labelled quantity bundles if props represent groups.

Reuse suitable accepted clips. Plan clip duration/model/estimated credits from the current account/tool information, not historic prices. Check current authorization before submissions; creating a skill, connecting MCP or approving an old film does not authorize a new film's generation. Do not buy subscriptions/credits, switch to a paid API, or automatically regenerate.

## Generate, inspect, then edit

For Runway connection and task lifecycle read [Runway media MCP](references/runway.md). Use the media-generation server and existing OAuth subscription route. Tool registration, authentication, exposed tools and model/plan eligibility are separate checks. Keep task receipts and signed URLs private.

When a new action shot is needed, generate a reference-based first frame and inspect identity, paws, props and whole movement path. Then generate one short action per shot. Inspect start, transfer and completed result **before** using the shot. The prompt is not evidence of success. Reject/reassign wrong direction, duplication, morphing and incomplete transfers; do not repeatedly spend credits to hide failure. Record accepted source-in/out and actual completion time.

Read [editing and verification](references/editing.md) and [the manifest schema](references/manifest.md) for local assembly. The portable implementation is `scripts/render.py` with `scripts/graphics.py`; `assets/film.example.json` shows the contract. Keep existing project renderer if it already satisfies these invariants; use the portable one for a new project or adapt its manifest to the existing renderer.

- Default production baseline: 1920×1080, 24fps, a large unobstructed action stage, one compact active explanation/calculation panel, Korean captions below. Match the approved benchmark's softness, palette and typography.
- Source speed is **1.0**. No stretching a short clip over long narration, reverse playback or repeated filler loops. Cut to a meaningful next action or detail view when narration is longer.
- Reuse approved clean narration. Separate local Korean captions, menus, equations and actual UI from generated imagery. Delay **all** audio channels equally (`adelay=250:all=1`), not just the first stereo channel.
- Show numbers changing at the inspected physical completion time; do not claim an uncompleted action. Clearly distinguish implemented behavior from planned integrations and settlement confirmation from actual payment.

## Finish with evidence and a usable result

Validate source intervals, complete cuts, exact arithmetic, captions and current/planned labels. Inspect the actual final frames and listen to representative final audio when a playback surface is available. Check whole-file decoding, loudness and stereo lag; ASR text agreement alone cannot prove good audio. Report any playback/inspection limitation accurately.

Keep the old film, deliver MP4 + SRT + chapter metadata + reproducible source/manifest, and update the project handoff with actual credits and lessons. Share through the project's approved delivery route; for local HTML use the approved private-network address and verify HTTP/Range responses. Do not expose source projects or credentials through a file server. Leave a review server only while the user is reviewing it.

This skill preserves a tested method and acceptance criteria. Generated motion and voice remain probabilistic: compare new output to the stored benchmark and reject material drift rather than promising bit-identical generation.

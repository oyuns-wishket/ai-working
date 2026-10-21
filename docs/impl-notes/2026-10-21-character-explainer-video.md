# Character explainer video workflow

## Goal and gate evidence
- User requested converting an accepted character-led educational film's design, production code and corrections into a reusable skill and applying it to this SSOT.
- Scope: reusable workflow, portable local compositor and validation, machine-local identity profile, documentation and bootstrap links. No new media generation, credits or subscription purchases.
- Preserve the accepted reference character and warm Korean voice via a machine-local registry. Keep source film, business facts, account data and signed provider URLs outside this public repository.
- Work in the canonical personal SSOT checkout on its existing main branch under the personal synchronization exception; initial tree clean.

## Design
- New owner `character-explainer-video`: character-led explanatory films with physical demonstrations. `design-workflow` retains new visual-direction decisions; its graphics reference routes accepted production to this skill.
- Deterministic renderer is manifest-driven: exact source intervals at 1x, separate narration, all-channel delay, captions, semantic side panel and timed prop labels. Runtime profiles locate original assets without public binaries or personal paths.
- Existing implementation and successful physical-action clips informed the recipe. Exclude failed generated actions rather than claiming prompt instructions were achieved. Generation output is stochastic; preserve references and benchmark evaluation, not a promise of identical output.

## Plan and verification
1. Extract instructions, prompts, schema and deterministic code without customer facts.
2. Register the existing accepted identity locally; render a free synthetic smoke film and check timing, stereo lag and missing-assets/unsafe-speed failures.
3. Independent behavioral review, skill/public audit, hook/bootstrap tests, then bootstrap and verify both native agent directories resolve to the canonical skill.
4. Record actual results and publication status below.

## Deviations
Independent review found an old organization label in a copied icon, repair-only routing gaps and weak final-media validation. These were removed/fixed before publishing. A local smoke run also reproduced AAC padding accumulation when independently encoded scene tracks were stream-copied; final assembly now aligns decoded scene audio to exact frame durations and encodes one continuous track. No paid media was generated.

## Results
- New skill includes identity/voice direction, actual-action review, media MCP/OAuth boundaries, manifest schema, portable compositor/graphics, profile/dependency inspection, contact sheets and final verifier.
- Existing character registered in a private local profile with original image copy, approved voice/benchmark/source pointers and76-file original-renderer dependency inventory. Public files contain no customer content, reference binary, account or machine paths.
- `python3 -m unittest discover -s skills/character-explainer-video/tests -p 'test_*.py'`:8 PASS. `node --test tests/*.test.mjs`:55 PASS, including bootstrap. Root Python tests:90 PASS.
- Two-scene free local fixture:1920×1080/24fps,144frames, Korean glyph/layout review, full decode, chapter metadata, exact final video frame sequence. Each source→rendered audio channel delay250ms; scene-assembly→final audio delay0ms, correlation0.9943. Wrong final-file substitution rejected.
- Periodic-tone fixture produced `unverified-ambiguous` rather than a false alignment pass; replaced test signal with deterministic broadband noise for confident timing measurement. This is a diagnostic fixture, not narration quality evidence.
- Independent scenario review covered new film, audio-only repair, missing reference, wrong action, static slides and setup-only scope. No additional installation blocker after fixes. Output hashes also bind scene receipts against replacement.
- Skill validation25 PASS; public contents/history audit PASS with new files staged; shell syntax/diff whitespace PASS. Bootstrap changed only the two new native skill links; status74 healthy. Claude and Codex resolve the same canonical directory.
- User requested applying the reusable workflow to the named SSOT. Commit/push covers only these reviewed public-safe skill/docs/CI changes; character assets and project source remain local. Remote CI result is checked after push. No application deployment or customer-system change.

## Remaining limits
- New model generations cannot guarantee bit-identical motion or speaker identity. The local benchmark and visual/audio acceptance checks preserve the method and expose drift. Remote models/prices/tool schemas must be checked at use time.
- A new session may be needed to refresh the native skill catalog. Another machine must pull/bootstrap and receive its own authorized local profile/assets; no personal paths or credentials synchronize via public Git.

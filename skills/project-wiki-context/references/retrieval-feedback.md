# Retrieval feedback

Measure the use of bounded project knowledge within the existing development task. This is not another wiki approval flow, a transcript collector or a productivity score.

## Start

Use the normal resolver with `route --record --sample-kind development`. It returns `retrieval_feedback.trace_id` alongside the same bounded document selection. Keep this ID in the current task context. Use `evaluation` for curated search tests and `maintenance` for wiki/environment administration. Do not relabel samples afterward to improve a result.

Recording is explicit. Without `--record`, routing remains read-only. Traces live under `~/.local/state/ai-working/wiki-feedback/`, or the machine-local `AI_WORKING_WIKI_FEEDBACK_STATE` override, outside Git with owner-only permissions. No network service, hook, API credential, query text, document body or provider conversation log is used. Project identity and evidence references are hashed. Selected canonical stable IDs, normalized body fingerprints, selected line ranges and byte/latency counts remain private. Body fingerprints identify the checked text without retaining it; legacy routes without a fingerprint report null.

## Finish the same task

After checking the implementation/decision, run:

```bash
python3 <project-wiki-context-root>/scripts/retrieval_feedback.py feedback \
  --trace-id <returned-id> --outcome used --document-id <selected-stable-id> \
  --evidence-kind test --evidence-ref <existing-verification-reference>
```

- `used`: a selected document influenced an actually checked decision. Name the used document IDs and existing code/test/deployment/decision evidence.
- `not_used`: the documents were not used; this is not automatically a retrieval failure.
- `missing`: needed knowledge was absent. Link the requirement or verification evidence that exposed the gap.
- `incorrect` / `outdated`: selected knowledge disagreed with checked evidence. Name the affected selected document IDs; do not silently rewrite the wiki or reset its verification date.
- `unknown`: the task ended without an observable conclusion.

The recorder only retains the evidence-reference hash. Put the readable evidence locator and trace ID in the project's existing implementation note/HANDOFF when recording a meaningful decision or defect; do not create another project log directory. `--actor agent` is the default and means an agent-reported observation, not a user satisfaction vote. Use `--actor human` only for an actual user report. Never invent a feedback event or copy another session's trace.

Feedback is final for that trace. Parallel attempts cannot overwrite it. A refused or unavailable measurement must not block product work, trigger more permissions, or cause a fake success entry. Existing knowns rules independently govern wiki writes.

## Report

```bash
python3 <project-wiki-context-root>/scripts/retrieval_feedback.py report --kind development
```

Report each outcome and feedback coverage. Unreported traces are unknown, not successful uses. Evaluation and maintenance are separate reports. A bounded report discloses truncation and invalid records. The measured latency is the route operation, not model response time or total task time. Token cost/cache savings, avoided bugs and causal productivity gains cannot be inferred from these counts. Use the existing task metrics separately when actual provider usage evidence is available.

For an initial rollout, verify privacy and recording with evaluation samples, then collect real development observations. Do not call the system effective merely because the recorder or six curated queries pass tests. Review repeatedly missing/incorrect/outdated topics and revalidate their owning knowledge separately.

# Verification

For `audit`, preserve the main skill's read-only boundary: inspect existing source, running screens and already available detectors. Do not install tools, run package-fetching commands below, or write project artifacts; report unavailable checks as gaps. The implementation sequence below applies when changes are authorized.

## Gate order

### 1. Project checks

Run the commands defined by the project and its package manager:

- lint
- typecheck when separate
- targeted tests
- full tests when practical
- production build

Report command, exit code, and relevant counts. Do not claim completion from code inspection alone.

### 2. Source detector

```bash
npx --yes impeccable@3.4.0 detect <source-path>
npx --yes impeccable@3.4.0 detect --json <source-path>
```

Exit codes:

- `0`: no findings
- `2`: findings detected
- `1`: command failure

Classify code `2` findings instead of reporting the scan as crashed.

### 3. Rendered detector

Start the project by its documented command, confirm the URL returns successfully, then run:

```bash
npx --yes impeccable@3.4.0 detect <url>
```

URL scan may require browser dependencies. If unavailable, disclose that rendered detector was not completed; Playwright screenshots do not replace detector coverage.

### 4. Playwright matrix

At minimum:

| Surface | Desktop | Mobile |
|---|---:|---:|
| target happy path | required | required when responsive |
| loading/empty/error | relevant states | relevant states |
| navigation open/closed | when changed | when changed |

Capture before and after at identical viewport, data, route, theme, and authentication state.

Check:

- no console errors introduced
- no failed relevant requests
- no unexpected horizontal scroll
- no clipped or overlapped text
- focus order and focus-visible
- hover/active/disabled/loading states
- reduced motion
- zoom and long Korean text when relevant

### 5. Context consistency

Compare the result against:

- product job and audience
- `DESIGN.md` token usage
- existing or approved typography
- density and layout rules
- explicit anti-pattern list
- small-feature scope guard
- interactive motion/chart choice or reused approved pattern
- actual 3D asset review and selected external capabilities, when relevant

### 6. Final evidence

Report:

- before/after routes or screenshots
- changed files and scope
- build/lint/test results
- detector counts by severity/rule
- intentional findings and reasons
- untested states and why
- plan deviations

## Purpose-specific acceptance

Apply only the selected purpose's checks from [data-surfaces.md](data-surfaces.md) or [motion-and-3d.md](motion-and-3d.md). Ordinary forms do not need a 3D performance audit.

- Data: verify Bklit implementation or documented exception against the chosen same-data preview; reconcile source totals with cards/charts/tables and test filters/missing/error states. Screenshots do not prove numerical correctness.
- Motion: use [motion-design.md](motion-design.md); run the approved representative task, continuous input, keyboard/touch, reduced motion and route cleanup. Check actual imports/use, not package presence alone.
- 3D: use [ai-assisted-3d.md](ai-assisted-3d.md); verify editable source and real exported asset, multi-angle appearance/parts/materials/clips, and actual web integration. Test forward/back scroll, resize, restored scroll, route re-entry, mobile, reduced motion, and asset failure/fallback. A generated model or static screenshot is not a completed website.
- External capabilities: distinguish user-reported plan, current official documentation and actual successful access. Confirm output rights/attribution, required format, hosting and decoder/runtime requests match the chosen path; no accidental paid API or restricted/free export assumption.
- Work UI: complete the main task with keyboard and pointer; verify feedback, preserved input, and recovery from failure.
- Marketing/content: check reading order, working CTA, accessible HTML content, relevant title/description and image/font loading. Do not create an SEO migration outside the requested scope.

## Final quality review

Use [web-quality.md](web-quality.md). Compare the same route, viewport, data and state against the approved comp or existing design authority. Check shared alignment axes, typography, spacing, numerical formatting, and primary action clarity. Include narrow content-failure widths, long text and zoom where relevant, not only two convenient screenshot sizes.

Record one representative user action → visible response → completion result. For performance-sensitive changes, record device/network/cache conditions and measured before/after results. Core Web Vitals field thresholds and lab observations are different evidence; do not claim field INP from a Lighthouse load test.

Fix observed in-scope issues, rerun affected checks, then finish when acceptance criteria pass. Do not loop indefinitely for arbitrary aesthetic scores. If a required check cannot run, disclose the exact gap; a screenshot or source review is not a substitute. Keep optional polish separate from blocking defects and preserve user-approved intentional findings.

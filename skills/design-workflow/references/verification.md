# Verification

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

### 6. Final evidence

Report:

- before/after routes or screenshots
- changed files and scope
- build/lint/test results
- detector counts by severity/rule
- intentional findings and reasons
- untested states and why
- plan deviations

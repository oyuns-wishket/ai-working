# Branching sandbox — git × Supabase × Vercel

- Each PR runs sandbox-like with an **ephemeral** Supabase preview branch (open→create, merge/close→delete). Never always-on (cost ~$9.6/mo each).
- Flow: pull main migrations → apply pending → seed (`seed.sql`) → verify `supabase migration list` (repair on divergence).
- Vercel preview is automatic per PR. Apply DB migration only after the preview deploy is READY (avoid env race).
- `supabase db push` is gated (ask) — run `--dry-run` first.

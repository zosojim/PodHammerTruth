# Intake service

This Cloudflare Worker stages opt-in observations before publication. It stores
no GitHub credential and never publishes automatically. Maintainers export the
pending batch, run the repository validator, review it, and merge it through the
same public workflow as manual contributions.

## Production

- Worker: `podhammer-truth-intake`
- Endpoint: `https://podhammer-truth-intake.podhammer-truth-intake.workers.dev`
- D1 database: `podhammer-truth` (Western Europe)
- Cloudflare account: the project owner's personal account

Health checks are public at `GET /health`. Observations are accepted at
`POST /v1/observations`; a successful response returns a one-time withdrawal
receipt. Passing that receipt as a Bearer token to
`DELETE /v1/observations/{run_id}` marks the staged observation withdrawn.
Only maintainers can call `GET /v1/export` with the export token.

## First deployment

```bash
cd intake
npm install
cp wrangler.toml.example wrangler.toml
npx wrangler login
npx wrangler d1 create podhammer-truth
# Copy the returned database ID into wrangler.toml.
npx wrangler d1 migrations apply podhammer-truth --remote
npx wrangler secret put INTAKE_PEPPER
npx wrangler secret put EXPORT_TOKEN
npm run check
npx wrangler deploy
```

`INTAKE_PEPPER` and `EXPORT_TOKEN` must be independently generated random
values. The Worker hashes the connecting address with the pepper solely for a
one-hour anti-abuse limit; raw addresses are not written to D1. Withdrawal
receipts are returned once and stored only as SHA-256 hashes.

The production export token is stored in the owner's macOS login keychain as
service `PodHammerTruth.ExportToken` and account `podhammer-truth`. Rotate it
without printing it with:

```bash
truth_export_token=$(openssl rand -hex 32)
printf '%s' "$truth_export_token" | npx wrangler secret put EXPORT_TOKEN
security add-generic-password -U -a podhammer-truth \
  -s PodHammerTruth.ExportToken -w "$truth_export_token" >/dev/null
unset truth_export_token
```

Deployments use the committed `wrangler.toml`, whose D1 identifier is public
configuration rather than a credential. Secret values belong only in
Cloudflare and the login keychain.

The Worker performs a narrow admission check. Repository publication still
requires the complete JSON Schema validation and secret scan.

# Intake service

This Cloudflare Worker stages opt-in observations before publication. It stores
no GitHub credential and never publishes automatically. Maintainers export the
pending batch, run the repository validator, review it, and merge it through the
same public workflow as manual contributions.

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

The Worker performs a narrow admission check. Repository publication still
requires the complete JSON Schema validation and secret scan.

# Pod Hammer Truth

Pod Hammer Truth is the public, reproducible evidence ledger for GPU workload
recipes and launch timing observations contributed by Pod Hammer users.

The repository keeps three kinds of facts separate:

- `recipes/` describes a versioned construction contract.
- `observations/` contains opt-in, secret-free measurements of what happened.
- `aggregates/` is generated from accepted observations and must never be
  edited by hand.

The human-readable dashboard is published with GitHub Pages. Every number on
the dashboard can be regenerated locally from the public observations.

## Privacy first

Observations must not contain credentials, IP addresses, SSH ports, provider
resource IDs, account IDs, volume IDs, private template names, commands,
captured output, prompts, or generated text. See [PRIVACY.md](PRIVACY.md).

## Validate and build

```bash
python3 scripts/validate.py
python3 scripts/aggregate.py --output aggregates/summary.json
python3 scripts/build_site.py --output _site
python3 -m unittest discover -s scripts/tests
```

## Contributing

Recipes and manual observation exports are accepted through pull requests.
Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting data. The future
automatic intake service lives in `intake/`; it is deliberately separate from
the public repository so no writable GitHub credential is shipped in the app.

## Evidence labels

- `imported`: manually supplied and schema-valid.
- `client-measured`: captured by Pod Hammer rather than typed by a person.
- `attested`: submitted by an App Attest-validated app instance.
- `maintainer-verified`: repeated under controlled cold-start conditions.

These labels describe provenance, not a guarantee that a provider will have
capacity or reproduce the same result.

## License

Code is released under the MIT License. Recipe and observation data is
released under CC0 1.0; see [LICENSE](LICENSE) and [LICENSE-DATA](LICENSE-DATA).

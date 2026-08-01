# Privacy

Participation is off by default. A user must explicitly export or contribute a
benchmark result. Public observations contain workload and infrastructure facts
needed for comparison, plus elapsed durations and a day-level date.

Public observations never intentionally contain:

- API tokens, Hugging Face tokens, backend keys, or SSH keys
- account, pod, instance, contract, volume, or private template identifiers
- IP addresses, hostnames, SSH ports, or forwarded URLs
- environment variable values, commands, terminal output, or error bodies
- character cards, chats, prompts, completions, or model input/output
- device identifiers, Apple Account information, or exact event timestamps

The selected provider data-center identifier is public because regional
comparison is the purpose of this dataset. Dates are reduced to UTC calendar
days. Each public observation uses a random per-run identifier and contains no
persistent contributor identifier.

The automatic intake service may temporarily retain an opaque anti-abuse key
and a withdrawal hash. Neither is exported to this public repository. A receipt
returned at submission time enables withdrawal without an account.

Repository history is durable. Maintainers can remove a record from the current
dataset and aggregation, but copies and forks already made by other people may
remain.

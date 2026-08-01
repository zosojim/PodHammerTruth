# Security

Report a suspected secret exposure privately to the repository owner instead
of opening a public issue. Do not include the exposed value in the report.

All contributions are scanned for common token, private-key, IP-address, and
connection-string patterns. Pattern scanning is defense in depth, not proof
that arbitrary text is safe. Observation schemas therefore reject free-form
commands and logs entirely.

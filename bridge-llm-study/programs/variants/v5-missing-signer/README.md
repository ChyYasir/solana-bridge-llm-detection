# v5 — Missing Signer

Copy of `bridge-secure`. One check removed, nothing else changed.

**Removed:** in `require_admin` (`processor.rs`), the `admin.is_signer` check.

**Effect:** admin-only instructions (`set_fee`, `set_paused`, `set_admin`, `withdraw_fees`)
still compare the supplied admin account's key against `config.admin`, but no longer
require that account to have actually signed. Since public keys are public, anyone can
pass the real admin's pubkey as an unsigned account and the check passes. The most serious
case is `set_admin`: an attacker calls it with the real admin's pubkey (unsigned) and a
`new_admin` they control, taking over the bridge.

**Group:** B — a well-documented Solana vulnerability class with no single named mega-incident
(Neodyme "Common Pitfalls").

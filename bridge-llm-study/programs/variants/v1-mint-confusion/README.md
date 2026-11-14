# v1 — Mint Confusion

Copy of `bridge-secure`. One check removed, nothing else changed.

**Removed:** in `lock`, the check that the claimed `collateral_mint` matches
`config.approved_collateral_mint` (`processor.rs`, right after the paused check, before the
vault-address derivation).

**Effect:** the vault a deposit lands in is an associated token account derived from
whatever mint is claimed — that derivation itself isn't a security boundary, the explicit
approved-mint check is. Without it, an attacker can claim any mint (including one they just
created, with no real value), get it accepted into its own freshly-derived vault account,
and have the bridge credit real wrapped tokens as if genuine collateral had been deposited.

**Design note:** the baseline was revised from an earlier single-fixed-vault design once we
realized the SPL Token program itself already enforces matching mints between any transfer's
source and destination — so a fixed vault with a fixed mint makes this check unconditionally
redundant, not exploitable. The corrected design (one vault per claimed mint, via a vault
PDA that owns associated token accounts) is what makes the approved-mint check load-bearing,
and is also the more faithful shape of how real multi-asset bridges actually work.

**Real-world precedent:** Cashio, March 2022, ~$52.8M.

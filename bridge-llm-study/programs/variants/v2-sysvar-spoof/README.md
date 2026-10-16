# v2 — Sysvar Spoofing

Copy of `bridge-secure`. The instructions-sysvar read in `release` is changed, nothing else.

**Changed:** `release` used `load_current_index_checked` / `load_instruction_at_checked`, which
verify the passed account is the real instructions sysvar before reading it. The variant instead
parses the account's bytes directly (`parse_sysvar_instruction`), without checking that the
account is the canonical instructions sysvar.

**Effect:** `release` trusts the relay's attestation by finding the Ed25519 verification
instruction in the transaction's instruction list, which it reads through the instructions
sysvar. Because the variant never checks that the supplied account is the real sysvar, an
attacker passes a fabricated account whose bytes look like an instruction list containing an
Ed25519 verification of the relay authority over the expected message. No Ed25519 instruction
actually ran, and the relay never signed — but `release` accepts the forged proof and mints
wrapped tokens. This is the Wormhole bug (Feb 2022, ~$326M): a signature-verification proof read
from an unchecked, attacker-supplied sysvar account.

**Group:** A — modelled on the Wormhole incident (see `Planning/attacks.md` and
`Planning/FINDINGS.md`).

# v6 — Arbitrary CPI

Copy of `bridge-secure`. One check removed and one program id unpinned; the CPI is rebuilt by
hand to allow that (below).

**Removed:** in `redeem` (`processor.rs`), the `check_token_program(token_program)?` guard.

**Changed:** the collateral-release CPI in `redeem` now targets the caller-supplied
`token_program.key` instead of the hardcoded `spl_token::id()`. Two supporting changes come with
it. The transfer instruction is built by hand (`AccountMeta`/`Instruction`, data `3` + amount),
because `spl_token::instruction::transfer` itself rejects any program id other than SPL Token.
And any accounts passed after the fixed ones are forwarded into `invoke_signed`, as programs that
pass on remaining accounts do; the attacker's program needs the real SPL Token program among them
to move the vault's tokens.

**Effect:** `redeem` signs the vault-out transfer with the vault-authority PDA. The secure
bridge only ever hands that signature to the real SPL Token program. The variant invokes
whatever program the caller passes as `token_program`, with the vault account and the PDA's
signature forwarded to it. An attacker deploys a program that, on invocation, transfers the
vault's full balance to an account it controls, redeems a single wrapped token to trigger the
CPI, and drains the vault — the PDA signs for the attacker's code because the program id was
never checked.

**Group:** B — a well-documented Solana vulnerability class (unvalidated program id / CPI trust
boundary) with no single named mega-incident.

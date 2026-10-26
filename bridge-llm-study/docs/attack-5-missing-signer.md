# Attack 5: Missing Signer Check

Group B, a formulated vulnerability class with no specific named incident behind it.

## Scope & setup

The program under test is a lock-and-mint bridge we wrote in native Rust; it is not Solana's
own source code. Solana is the platform (runtime, validator, SPL Token program), and we use
its toolchain and SDK (`solana-program`, `cargo build-sbf`, `solana-test-validator`) to build
and run our program on a local chain. The missing signer check is an application-level flaw:
Solana does not enforce that a privileged account actually signed the transaction, so the
class is reachable in any native program that names an authority account but never checks its
signature.

## The bug

Admin-only instructions check that the caller matches the stored admin. The secure bridge also
requires that admin account to have signed the transaction. The vulnerable copy drops only that
signer check.

## The attack and its outcome

The attacker calls `set_admin`, passing the real admin's public key as an account but without
the admin's signature, and names themselves as the new admin.

- Against the vulnerable copy the attack succeeds: admin authority transfers from the real
  admin to the attacker in a single transaction.
- Against the secure bridge it is rejected (`MissingSignature`, error `0xc`).

## How detection is tested

Each model is given one of two kinds of input and asked whether something is wrong, with no
hint about what to look for:

- **Source Code** — the model reads the program's Rust source and must point at the missing
  signer check. This stands in for a pre-deployment audit.
- **Transaction Information** — the model reads only the on-chain record of a session (the
  instructions, logs, and account balances, with no code) and must recognise an attack. This
  stands in for a monitor watching live activity.

"Detected" means the model named the real problem: the missing signer check when reading the
Source Code, or the admin takeover when reading the Transaction Information. "False alarm"
means it flagged clean input as an attack — the secure code on the Source Code track, or a
legitimate operation on the Transaction Information track. The benign Transaction Information
case is an honest admin rotation: the real admin hands control to a new key with a properly
signed `set_admin`. It changes the admin exactly as the attack does, but legitimately, so it is
the fair test of whether a model flags the mechanics or the actual abuse. "Blocked attempt"
counts how often the model flagged the rejected attack as an attack. Counts are out of 100 runs
per cell. An answer counts as "Detected" only when it names the actual planted bug — the missing
`admin.is_signer` check — not merely that something looks wrong.

## Results (100 runs per cell)

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 10 / 100 | 50 / 100 | 100 / 100 | 100 / 100 | 0 / 100 |
| DeepSeek-V3.2 | 0 / 100 | 100 / 100 | 100 / 100 | 100 / 100 | 78 / 100 |
| Llama-3.3-70B | 0 / 100 | 100 / 100 | 0 / 100 | 57 / 100 | 100 / 100 |

## Reading

All four models caught the attack from the Transaction Information every single run (100 of
100) and named it correctly: the stored admin was reassigned to the attacker's address in one
instruction. All four also flagged the blocked attempt almost always (gpt-oss 85 of 100, the
other three 100 of 100), reading the rejected instruction as an attempted exploit — which it is.

The benign case is the one that qualifies this. When the real admin legitimately rotates
control to a new key with a properly signed `set_admin`, all four models flag it too — 100 of
100, every model, including gpt-oss, which false-alarmed on Attack 1's honest session only 4 of
100. In other words, on this attack no model distinguishes a legitimate admin rotation from the
takeover: the admin address changing is what they react to, and a signed handoff looks the same
to them as an unsigned seizure. Their perfect score on the real attack is therefore partly just
"flag any admin change," not evidence they understood the missing signature. The signal that
actually separates the two — who signed the transaction — is present in the record but goes
unused.

The Source Code is the hardest version of this attack for every model. The planted bug is that
`require_admin` checks the admin's key but never `admin.is_signer`, so any caller can pass the
admin's public key unsigned. gpt-oss found it 10 of 100 — low, but it is the only model that
named it at all. DeepSeek, Qwen, and Llama each found it 0 of 100. They flag the vulnerable code
readily (100 of 100) but name a different bug: Qwen points at a signature check in an unrelated
CPI, DeepSeek at token-account ownership, Llama at arithmetic overflow or reentrancy — none at
the missing signer check. Those stock answers are what each model reaches for regardless of the
code, which is why a bare "yes" from them carries no information; only gpt-oss stays quiet on
clean code any of the time (false alarm 50 of 100), the same discrimination edge it showed on
Attack 1.

Two headlines. First, the missing-signer check is the hardest bug to read in source of anything
tested: only the one model that genuinely audits code (gpt-oss) names it, and even it manages
only 10 of 100, while the other three never identify it and fall back on a default answer. That
is the opposite of a famous named hack like Wormhole, where the pattern is so recognisable that
every model names it — which is exactly why the Group B classes are worth measuring separately.
Second, the Transaction Information track splits the models in two. The admin takeover shows up
as a real on-chain state change — the stored admin key changes from one address to another — so
it is genuinely in the trace, not a planted label. gpt-oss and DeepSeek both read that change and
flag the takeover every run (100 of 100). But they flag a legitimate, signed admin rotation just
as hard (false alarm 100 of 100 each): they react to "the admin changed," not to whether it was
authorized, so they cannot tell a real takeover from an honest hand-off. Llama does the opposite
and worse — it misses the takeover entirely (0 of 100), reading the successful change as a normal
session, and only raises an alarm on the blocked attempt (100 of 100), reacting to that
transaction's error rather than to the admin change. So on this attack the readers detect the
behaviour but cannot judge its legitimacy, and the one model that keys on errors instead of state
fails to see the breach at all.

## Files

- Vulnerable copy: `programs/variants/v5-missing-signer/`
- Attack script: `client/src/exploits/exploit-v5.ts`
- Run everything: `scripts/run-attack-v5.sh`
- Records: `traces/v5-missing-signer/`
- Detection harness: `detection/run_study.py`
- Raw answers: `detection/results/v5-missing-signer-*.json` (scored copies in `results/graded/`)

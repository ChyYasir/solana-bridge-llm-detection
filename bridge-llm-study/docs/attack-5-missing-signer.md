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
per cell. An answer counts as "Detected" only when its main diagnosis names the actual planted
bug — the missing `admin.is_signer` check in the source, or the unauthorized admin change in the
trace — not merely that something looks wrong. Every answer was graded blind (model name
hidden, order shuffled) by Claude Opus 5.5 against the fixed rubric in
`detection/judge_prompt.md`; "False alarm" and "Blocked attempt" use the model's own yes/no.

## Results (100 runs per cell)

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 10 / 100 | 50 / 100 | 100 / 100 | 100 / 100 | 0 / 100 |
| DeepSeek-V3.2 | 0 / 100 | 100 / 100 | 100 / 100 | 100 / 100 | 78 / 100 |
| Llama-3.3-70B | 0 / 100 | 100 / 100 | 0 / 100 | 57 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 5 / 100 | 94 / 100 | 96 / 100 | 81 / 100 | 99 / 100 |

## Reading

Three of the four models catch the attack from the Transaction Information almost every run —
gpt-oss and DeepSeek 100 of 100, Nemotron 96 — and name it correctly: the stored admin key changed
from one address to another, an admin takeover. Here the visible change *is* the attack, so
noticing it and diagnosing it are the same thing. Llama is the exception and misses it entirely
(0 of 100).

The benign case is the one that qualifies this. When the real admin legitimately rotates
control to a new key with a properly signed `set_admin`, the same models flag it too — gpt-oss and
DeepSeek 100 of 100, Nemotron 81, even though gpt-oss false-alarmed on Attack 1's honest session
only once in 100. On this attack no model distinguishes a legitimate admin rotation from the
takeover: the admin address changing is what they react to. That is also all the trace can
offer them — it records the admin key before and after, but not who signed the transaction — so
from the record alone an honest hand-off and an unsigned seizure look the same. The high
detection on the attack is therefore "flag any admin change," not evidence the models understood
the missing signature.

The Source Code is the hardest version of this attack for every model. The planted bug is that
`require_admin` checks the admin's key but never `admin.is_signer`, so any caller can pass the
admin's public key unsigned. gpt-oss found it 10 of 100 and Nemotron 5 — low, and they are the
only models that named it at all. DeepSeek and Llama each found it 0 of 100. They flag the
vulnerable code readily (100 of 100) but name a different bug: DeepSeek points at token-account
ownership, Llama at arithmetic overflow or reentrancy, and many answers blame a signature check
in an unrelated CPI or the instructions sysvar in `release` — none at the missing signer check.
Those stock answers are what each model reaches for regardless of the code, which is why a bare
"yes" from them carries no information; only gpt-oss stays quiet on clean code any of the time
(false alarm 50 of 100), the same discrimination edge it showed on Attack 1.

Two headlines. First, the missing-signer check is the hardest bug to read in source of anything
tested: gpt-oss names it 10 of 100, Nemotron 5, and the other two never identify it and fall back
on a default answer. That
is the opposite of a famous named hack like Wormhole, where the pattern is so recognisable that
every model names it — which is exactly why the Group B classes are worth measuring separately.
Second, the Transaction Information track splits the models in two. The admin takeover shows up
as a real on-chain state change — the stored admin key changes from one address to another — so
it is genuinely in the trace, not a planted label. gpt-oss and DeepSeek both read that change and
flag the takeover every run (100 of 100), Nemotron 96. But they flag a legitimate, signed admin
rotation almost as hard (false alarm 100, 100 and 81): they react to "the admin changed," not to
whether it was authorized, so they cannot tell a real takeover from an honest hand-off. Llama does the opposite
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
- Detection harness: `detection/run_study.py`; grading rubric `detection/judge_prompt.md`, blinding and merge `detection/judge.py`
- Raw answers: `detection/results/v5-missing-signer-*.json` (scored copies in `results/graded/`)

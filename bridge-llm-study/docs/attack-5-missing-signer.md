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
per cell, scored by a deterministic rule-based grader (see `detection/GRADING.md`).

## Results (100 runs per cell)

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 15 / 100 | 50 / 100 | 100 / 100 | 100 / 100 | 85 / 100 |
| DeepSeek-V3.2 | 5 / 100 | 100 / 100 | 100 / 100 | 100 / 100 | 100 / 100 |
| Qwen3-235B | 73 / 100 | 100 / 100 | 100 / 100 | 100 / 100 | 100 / 100 |
| Llama-3.3-70B | 13 / 100 | 100 / 100 | 100 / 100 | 100 / 100 | 100 / 100 |

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

The Source Code is where this attack separates from Attack 1, and where the ranking inverts.
On Attack 1 gpt-oss was the only model that read the code, finding the mint-confusion bug 96 of
100. Here, against a plain formulated class with no public write-up, gpt-oss found the missing
signer check just 15 of 100. The standout is Qwen3-235B, which found it 73 of 100 — by far the
highest, and a reversal of its 0 of 100 on Attack 1. DeepSeek (5 of 100) and Llama (13 of 100)
stayed low.

But Qwen's source number has to be read next to its false-alarm column: it flagged the secure
code 100 of 100. It finds the planted bug often and also calls bug-free code vulnerable every
time, so a bare "yes" from Qwen carries no information — only the explanation does. The same
caveat applies to DeepSeek and Llama, which flagged secure code 100 of 100 as well. gpt-oss is
the only model that stayed quiet on clean code any of the time (false alarm 50 of 100), the
same discrimination edge it showed on Attack 1, even though its localization here is weak.

Two headlines. First, Source Code localization is noisy and does not transfer: the model that
read the code best on the famous hack (gpt-oss, 96 of 100 on Attack 1) is not the one that read
it best on the formulated class (Qwen, 73 of 100 here), which is exactly why the Group B classes
are worth measuring separately from the public-incident recall Attack 1 can reward. Second, the
Transaction Information track catches the attack reliably but with no discrimination on this
class — every model flags a legitimate admin rotation just as hard as the takeover. On Attack 1
the benign session separated the models (gpt-oss 4 of 100 vs. the rest at 100); here it
separates none of them. Catching the attack and crying wolf on honest privileged activity are,
for this class, the same behavior.

## Files

- Vulnerable copy: `programs/variants/v5-missing-signer/`
- Attack script: `client/src/exploits/exploit-v5.ts`
- Run everything: `scripts/run-attack-v5.sh`
- Records: `traces/v5-missing-signer/`
- Detection harness: `detection/run_study.py`, grader `detection/grade.py`
- Raw answers: `detection/results/v5-missing-signer-*.json`

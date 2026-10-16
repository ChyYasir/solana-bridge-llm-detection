# Attack 6: Arbitrary CPI

Group B, a formulated vulnerability class (unvalidated program id / CPI trust boundary) with no
specific named incident behind it.

## Scope & setup

The program under test is a lock-and-mint bridge we wrote in native Rust; it is not Solana's
own source code. Solana is the platform (runtime, validator, SPL Token program), and we use
its toolchain and SDK (`solana-program`, `cargo build-sbf`, `solana-test-validator`) to build
and run our program on a local chain. The flaw is application-level: Solana lets a program
invoke whatever program id it is handed, so any native program that forwards a caller-supplied
program id into a cross-program invocation without checking it is reachable by this class.

## The bug

When a user redeems collateral, the bridge moves tokens out of the vault with a cross-program
invocation signed by the vault-authority PDA. The secure bridge pins that call to the real SPL
Token program two ways: it checks `token_program.key == spl_token::id()` and it builds the
transfer against the hardcoded `spl_token::id()`. The vulnerable copy drops the check and builds
the transfer against the caller-supplied `token_program.key`, forwarding the vault account and
the PDA's signature to whatever program the caller named.

## The attack and its outcome

The attacker deploys a small program that, when invoked, transfers the full balance of the
account it is handed to an account it controls. They earn a single wrapped token, then call
`redeem` for that one token with their own program substituted for the token program. The bridge
signs the vault-out transfer with the PDA and hands it to the attacker's program, which drains
the entire vault.

- Against the vulnerable copy the attack succeeds: the vault goes from 100 collateral to 0 and
  the attacker's balance rises by the same amount in one transaction.
- Against the secure bridge it is rejected at `redeem` (`WrongTokenProgram`, error `0x7`).

## How detection is tested

Each model is given one of two kinds of input and asked whether something is wrong, with no
hint about what to look for:

- **Source Code** — the model reads the program's Rust source and must point at the unchecked,
  forwarded program id in the redeem CPI. This stands in for a pre-deployment audit.
- **Transaction Information** — the model reads only the on-chain record of a session (the
  instructions, logs, and account balances, with no code) and must recognise an attack. This
  stands in for a monitor watching live activity.

"Detected" means the model named the real problem: the unpinned token-program CPI when reading
the Source Code, or the vault being drained through an unexpected program when reading the
Transaction Information. "False alarm" means it flagged clean input as an attack — the secure
code on the Source Code track, or an honest redeem through the real SPL Token program on the
Transaction Information track. "Blocked attempt" counts how often it flagged the rejected attack
as an attack. Counts are out of 100 runs per cell, scored by a deterministic rule-based grader
(see `detection/GRADING.md`).

## Results (100 runs per cell)

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 94 / 100 | 50 / 100 | 100 / 100 | 30 / 100 | 43 / 100 |
| DeepSeek-V3.2 | 5 / 100 | 100 / 100 | 100 / 100 | 100 / 100 | 100 / 100 |
| Qwen3-235B | 11 / 100 | 100 / 100 | 99 / 100 | 100 / 100 | 100 / 100 |
| Llama-3.3-70B | 55 / 100 | 100 / 100 | 100 / 100 | 0 / 100 | 90 / 100 |

## Reading

All four models caught the drain from the Transaction Information almost every run (99–100 of
100) and described it correctly: the vault's whole balance left through a program that was not
the SPL Token program, carrying the vault authority's signature. The live attack is not the hard
part for any of them.

The Source Code track is where they separate, and the order is different again from the earlier
attacks. gpt-oss-120b found the unpinned, forwarded program id 94 of 100 — nearly as well as it
read the Cashio bug in Attack 1, and far ahead of everyone here. Llama-3.3-70B is second at 55
of 100, its best source showing across all three attacks. Qwen3-235B, which led the Source Code
track on Attack 5 at 73, dropped to 11 here; DeepSeek stayed at the bottom (5). So the model that
reads a given bug best keeps changing: gpt-oss on Attack 1, Qwen on Attack 5, gpt-oss then Llama
on Attack 6. Source-code skill is bug-specific, not a fixed ranking.

False alarms again decide how much a detection is worth. gpt-oss is the only model that shows
real restraint: on the Transaction Information it flagged the honest redeem 30 of 100 and the
blocked attempt 43 of 100, and on the Source Code it flagged the secure code about half the time
(50 of 100). Llama is the cleanest on honest live traffic — it never flagged the benign redeem
(0 of 100), the same behaviour it showed on Attack 1 — though it still flags all secure code and
most blocked attempts. DeepSeek and Qwen flag essentially everything (secure code, honest redeem,
blocked attempt all at or near 100 of 100), so their perfect trace detection carries weight only
through the explanation, not the bare yes.

The pattern from the earlier attacks holds: Transaction Information detection is reliable across
models, Source Code localization is noisy and its ranking does not transfer, and gpt-oss — the
only reasoning model of the four — is the one that both finds the bug and stays quietest on clean
input.

## Files

- Vulnerable copy: `programs/variants/v6-arbitrary-cpi/`
- Attacker's substituted program: `attacker-program/`
- Attack script: `client/src/exploits/exploit-v6.ts`
- Run everything: `scripts/run-attack-v6.sh`
- Records: `traces/v6-arbitrary-cpi/`
- Detection harness: `detection/run_study.py`, grader `detection/grade.py`
- Raw answers: `detection/results/v6-arbitrary-cpi-*.json`

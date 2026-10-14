# Attack 1: Mint Confusion

Group A, modelled on the Cashio incident (March 2022, ~$52.8M).

## Scope & setup

The program under test is a lock-and-mint bridge we wrote in native Rust; it is not Solana's
own source code. Solana is the platform (runtime, validator, SPL Token program), and we use
its toolchain and SDK (`solana-program`, `cargo build-sbf`, `solana-test-validator`) to build
and run our program on a local chain. The bug is an application-level flaw that Solana does
not prevent automatically, so the class is still reachable in current native programs that
skip the check. Cashio's own instance was patched after the hack; what we reproduce here is
the class, not that specific deployment.

## The bug

`lock` accepts a deposit and, in the secure bridge, checks that the deposited token is the
approved collateral mint. The vulnerable copy drops only that one check.

## The attack and its outcome

The attacker mints a worthless token of their own, deposits 500,000 of it, and the bridge
hands back 500,000 real wrapped tokens.

- Against the vulnerable copy the attack succeeds.
- Against the secure bridge it is rejected at `lock` (`WrongMint`, error `0x3`).

## How detection is tested

Each model is given one of two kinds of input and asked whether something is wrong, with no
hint about what to look for:

- **Source Code** — the model reads the program's Rust source and must point at the flawed
  check. This stands in for a pre-deployment audit.
- **Transaction Information** — the model reads only the on-chain record of a session (the
  instructions, logs, and account balances, with no code) and must recognise an attack. This
  stands in for a monitor watching live activity.

"Detected" means the model named the real problem: the missing `lock` check when reading the
Source Code, or the unbacked mint when reading the Transaction Information. "False alarm"
means it called the secure code or an ordinary user's session an attack. Counts are out of
100 runs per cell, scored by a deterministic rule-based grader (see `detection/GRADING.md`).

## Results (100 runs per cell)

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 96 / 100 | 51 / 100 | 99 / 100 | 4 / 100 | 5 / 100 |
| DeepSeek-V3.2 | 2 / 100 | 100 / 100 | 100 / 100 | 100 / 100 | 87 / 100 |
| Qwen3-235B | 0 / 100 | 100 / 100 | 100 / 100 | 100 / 100 | 100 / 100 |
| Llama-3.3-70B | 15 / 100 | 100 / 100 | 100 / 100 | 0 / 100 | 100 / 100 |

### Timing ablation (Transaction Information, timing shown vs. hidden)

Normal relay delay over 40 honest runs averaged 2.80s, with a mean-plus-3σ cut-off of 3.88s.
The attack's own delay was 2.89s, inside the normal band, so timing alone cannot separate it.
Each cell is "without timing / with timing".

| Model | Detected the attack | False alarm on normal | Flagged blocked attempt |
|---|---|---|---|
| gpt-oss-120b | 96 / 100 | 3 / 7 | 19 / 6 |
| DeepSeek-V3.2 | 99 / 99 | 100 / 100 | 66 / 79 |
| Qwen3-235B | 99 / 100 | 100 / 78 | 100 / 100 |
| Llama-3.3-70B | 100 / 100 | 0 / 0 | 100 / 100 |

## Reading

All four models caught the real attack from the Transaction Information almost every run
(99–100 of 100) and described the mechanics correctly: wrapped tokens minted against a deposit
held in a fake vault while the real vault stayed empty. Where they split is on false alarms and
on reading the Source Code.

gpt-oss-120b is the only model that both caught the attack and stayed quiet on clean input: on
the Transaction Information it false-alarmed on a normal session just 4 of 100 times, and on
the Source Code it found the planted bug 96 of 100 while flagging the secure code about half
the time (51 of 100). It is the only model that meaningfully reads the code.

DeepSeek-V3.2 and Qwen3-235B sit at the opposite end. Both flagged essentially everything:
secure code 100 of 100, and a normal user's session 100 of 100. Their detection count is only
meaningful because the explanation on the real attack matches what happened; a bare yes from
either carries no weight. Neither found the planted bug in the Source Code (DeepSeek 2, Qwen 0).

Llama-3.3-70B is a middle case. It caught the attack every run and, unlike DeepSeek and Qwen,
never false-alarmed on a normal session (0 of 100), though it still flagged the blocked
attempt every time. On the Source Code it found the planted bug a little more than those two
(15 of 100) but still flagged the secure code in every run.

Timing changed little for any model. For DeepSeek it only nudged blocked-attempt flags up
(66 to 79). For Qwen the one visible effect was on normal sessions, where showing the timing
cut false alarms from 100 to 78. For Llama it changed nothing, and for gpt-oss it only moved
the already-low blocked-attempt flags (19 to 6). None of this changes whether the real attack
is caught, which is expected for an attack that never has to wait.
Cashio is a well-known hack the model may have seen before; the Group B attacks (5, 6, 7)
test whether the behaviour holds without that advantage.

## Files

- Vulnerable copy: `programs/variants/v1-mint-confusion/`
- Attack script: `client/src/exploits/exploit-v1.ts`
- Run everything: `scripts/run-attack-v1.sh`
- Records: `traces/v1-mint-confusion/`, normal-delay baseline in `traces/recon/`
- Detection harness: `detection/run_study.py`, grader `detection/grade.py`
- Raw answers: `detection/results/v1-mint-confusion-*.json`

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
| gpt-oss-120b | pending | pending | pending | pending | pending |
| DeepSeek-V3.2 | 2 / 100 | 100 / 100 | 100 / 100 | 100 / 100 | 87 / 100 |
| Qwen3-235B | 0 / 100 | 100 / 100 | 100 / 100 | 100 / 100 | 100 / 100 |
| Llama-3.3-70B | 15 / 100 | 100 / 100 | 100 / 100 | 0 / 100 | 100 / 100 |

### Timing ablation (Transaction Information, timing shown vs. hidden)

Normal relay delay over 40 honest runs averaged 2.80s, with a mean-plus-3σ cut-off of 3.88s.
The attack's own delay was 2.89s, inside the normal band, so timing alone cannot separate it.
Each cell is "without timing / with timing".

| Model | Detected the attack | False alarm on normal | Flagged blocked attempt |
|---|---|---|---|
| gpt-oss-120b | pending | pending | pending |
| DeepSeek-V3.2 | 99 / 99 | 100 / 100 | 66 / 79 |
| Qwen3-235B | 99 / 100 | 100 / 78 | 100 / 100 |
| Llama-3.3-70B | 100 / 100 | 0 / 0 | 100 / 100 |

## Reading so far

DeepSeek-V3.2 and Qwen3-235B behave almost identically. Both caught the real attack from the
Transaction Information in every run and described it correctly, but both also called a normal
user's session an attack in every run. The detection number is only meaningful because the
explanation on the real attack matches what actually happened; on its own, a yes from either
model carries little weight. Reading the Source Code, neither found the planted bug in any
meaningful way (DeepSeek 2 of 100, Qwen 0 of 100) while flagging the secure code every time,
so neither distinguishes the vulnerable copy from the safe one.

Llama-3.3-70B behaves differently on the Transaction Information. It also caught the attack in
every run, but unlike the other two it did not false-alarm on a normal session even once
(0 of 100). It did still flag the blocked attempt every time. On the Source Code it found the
planted bug a bit more often than the others (15 of 100) but still flagged the secure code in
every run.

Timing barely moved any model. For DeepSeek it only nudged the blocked-attempt flags up
(66 to 79). For Qwen the one visible effect was on normal sessions: showing the timing cut its
false alarms from 100 to 78, the only case so far where timing made a model more cautious
rather than less. For Llama timing changed nothing. None of these effects changes whether the
real attack is caught, which is expected for an attack that never has to wait.

Results for gpt-oss-120b will be added once that run completes.
Cashio is a well-known hack the model may have seen before; the Group B attacks (5, 6, 7)
test whether the behaviour holds without that advantage.

## Files

- Vulnerable copy: `programs/variants/v1-mint-confusion/`
- Attack script: `client/src/exploits/exploit-v1.ts`
- Run everything: `scripts/run-attack-v1.sh`
- Records: `traces/v1-mint-confusion/`, normal-delay baseline in `traces/recon/`
- Detection harness: `detection/run_study.py`, grader `detection/grade.py`
- Raw answers: `detection/results/v1-mint-confusion-*.json`

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
100 runs per cell. On both tracks, an answer counts as "Detected" only when it names the actual
planted bug — the missing collateral-mint check — not merely that something looks wrong.

## Results (100 runs per cell)

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 95 / 100 | 51 / 100 | 5 / 100 | 1 / 100 | 0 / 100 |
| DeepSeek-V3.2 | 0 / 100 | 100 / 100 | 34 / 100 | 99 / 100 | 66 / 100 |
| Llama-3.3-70B | 0 / 100 | 100 / 100 | 0 / 100 | 0 / 100 | 100 / 100 |

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

On the Source Code, only gpt-oss-120b reads the program: it found the missing mint check 95 of
100 while flagging the secure code about half the time (51 of 100). DeepSeek and Llama each found
it 0 of 100 — DeepSeek names a token-account ownership issue in the wrong function, Llama answers
"arithmetic overflow" or "reentrancy" regardless of the code in front of it — and both flag the
secure code every run, so a bare "yes" from either carries no weight.

The Transaction Information track is where this attack is genuinely hard, once the trace is read
on its on-chain facts rather than on labels. The tell is that wrapped tokens are minted while the
approved-collateral vault stays at 0 — the deposit went in as a different, unapproved mint. gpt-oss
notices that only 5 of 100; the rest of the time it reads the single shared nonce on the lock and
the release as a "replay" bug and misses the mint entirely. DeepSeek does best at 34 of 100 — it
is the one that points at the empty approved-collateral vault — but it still flags the honest
session 99 of 100 and the blocked attempt 66, so its detection comes wrapped in heavy false
alarms. Llama detects it 0 of 100: it calls the successful attack a normal bridge session and
only raises an alarm on the blocked attempt (100 of 100), reacting to the failed transaction's
error rather than to the forgery that succeeded.

The low numbers are the real result. On an earlier version of this trace that carried descriptive
field labels, every model scored near-perfect (99–100); stripping those labels so the trace shows
only what a monitor would actually see — instructions, logs, balances — dropped detection sharply,
which means the apparent skill was reading the labels, not the activity.

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
- Detection harness: `detection/run_study.py`
- Raw answers: `detection/results/v1-mint-confusion-*.json` (scored copies in `results/graded/`)

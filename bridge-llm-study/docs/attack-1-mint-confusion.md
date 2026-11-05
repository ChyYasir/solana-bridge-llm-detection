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
100 runs per cell. On both tracks, an answer counts as "Detected" only when its main diagnosis
names the actual planted bug — the missing collateral-mint check, or the unbacked mint it
produces — not merely that something looks wrong. Every answer was graded blind (model name
hidden, order shuffled) by Claude Opus 5.5 and, independently, by Gemini 3.8 Flash against the fixed rubric in
`detection/judge_prompt.md`; "False alarm" and "Blocked attempt" use the model's own yes/no.

## Results (100 runs per cell)

Two graders scored the "Detected" columns independently, each blind (model name hidden, order
shuffled) against `detection/judge_prompt.md`: Claude Opus 5.5 (`claude-opus-5-5`) and Gemini 3.8
Flash (`gemini-3.8-flash`). "False alarm" and "Blocked attempt" are the tested models' own
yes/no answers, so they are the same in both tables. The Reading below uses the Claude numbers.

### Graded by Claude Opus 5.5

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 96 / 100 | 51 / 100 | 0 / 100 | 1 / 100 | 0 / 100 |
| DeepSeek-V3.2 | 2 / 100 | 100 / 100 | 3 / 100 | 99 / 100 | 66 / 100 |
| Llama-3.3-70B | 5 / 100 | 100 / 100 | 0 / 100 | 0 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 39 / 100 | 97 / 100 | 3 / 100 | 1 / 100 | 100 / 100 |
| Gemma-4-31B (thinking) | 90 / 100 | 98 / 100 | 1 / 100 | 75 / 100 | 20 / 100 |

### Graded by Gemini 3.8 Flash

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 96 / 100 | 51 / 100 | 0 / 100 | 1 / 100 | 0 / 100 |
| DeepSeek-V3.2 | 2 / 100 | 100 / 100 | 5 / 100 | 99 / 100 | 66 / 100 |
| Llama-3.3-70B | 5 / 100 | 100 / 100 | 0 / 100 | 0 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 39 / 100 | 97 / 100 | 1 / 100 | 1 / 100 | 100 / 100 |
| Gemma-4-31B (thinking) | 90 / 100 | 98 / 100 | 7 / 100 | 75 / 100 | 20 / 100 |

The two graders agreed on 796 of 800 answers for this attack: all 400 on the Source Code
(Cohen's kappa 1.00) and 396 of 400 on the Transaction Information (kappa 0.66, from 4
borderline answers). I adjudicated those 4; the adjudicated labels match the Claude table.

### Timing ablation (Transaction Information, timing hidden vs. shown)

The traces above have every timing field removed. Here the same three sessions were run again,
100 times each, with the step times (submitted, confirmed, slot) left in, together with the
session's relay delay and the normal range measured over 40 honest runs (mean 2.85s, mean-plus-3σ
cut-off 3.82s). The attack's own delay was 2.94s, inside the normal band, so timing alone cannot
separate it. "Timing hidden" repeats the numbers from the tables above. "Detected" is scored by
each grader as above; "False alarm" and "Blocked attempt" are the models' own yes/no, so they are
the same in both tables.

#### Graded by Claude Opus 5.5

| Model | Timing hidden · Detected | Timing shown · Detected | Timing hidden · False alarm | Timing shown · False alarm | Timing hidden · Blocked attempt | Timing shown · Blocked attempt |
|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 / 100 | 0 / 100 | 1 / 100 | 60 / 100 | 0 / 100 | 5 / 100 |
| DeepSeek-V3.2 | 3 / 100 | 13 / 100 | 99 / 100 | 100 / 100 | 66 / 100 | 35 / 100 |
| Llama-3.3-70B | 0 / 100 | 0 / 100 | 0 / 100 | 0 / 100 | 100 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 3 / 100 | 0 / 100 | 1 / 100 | 1 / 100 | 100 / 100 | 97 / 100 |
| Gemma-4-31B (thinking) | 1 / 100 | 0 / 100 | 75 / 100 | 97 / 100 | 20 / 100 | 100 / 100 |

#### Graded by Gemini 3.8 Flash

| Model | Timing hidden · Detected | Timing shown · Detected | Timing hidden · False alarm | Timing shown · False alarm | Timing hidden · Blocked attempt | Timing shown · Blocked attempt |
|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 / 100 | 0 / 100 | 1 / 100 | 60 / 100 | 0 / 100 | 5 / 100 |
| DeepSeek-V3.2 | 5 / 100 | 74 / 100 | 99 / 100 | 100 / 100 | 66 / 100 | 35 / 100 |
| Llama-3.3-70B | 0 / 100 | 0 / 100 | 0 / 100 | 0 / 100 | 100 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 1 / 100 | 5 / 100 | 1 / 100 | 1 / 100 | 100 / 100 | 97 / 100 |
| Gemma-4-31B (thinking) | 7 / 100 | 1 / 100 | 75 / 100 | 97 / 100 | 20 / 100 | 100 / 100 |

The graders agreed on 334 of the 400 timing-shown attack answers (kappa 0.24). All 66
disagreements are the same kind of answer, almost all from DeepSeek: it points at the approved
vault sitting at 0 while 500,000 wrapped tokens were minted, then concludes the deposit was not
properly approved or verified. Claude reads that as a missing-authorization diagnosis and marks it
incorrect; Gemini accepts it. I adjudicated all 66 with one rule: an answer is correct when its
finding says the wrapped tokens were minted without backing (no collateral or locked funds behind
them), and incorrect when it only names a missing approval or authorization step. That keeps 10 of
them as correct, so the adjudicated timing-shown Detected is DeepSeek 21 and Nemotron 2 (all other
cells as in the Claude table). The list, with each decision, is in
`detection/judging/disagreements-timing-claude-opus-5-5-vs-gemini-3.8-flash.md`.

Gemma-4-31B was added later as a reasoning model (thinking on). Its answers were graded in the
same way in their own blind pool (`detection/judging-gemma/`); the agreement counts above cover
the other four models. The two graders agreed on 593 of Gemma's 600 answers for this attack. The 7
disagreements (6 on the Transaction Information, 1 with timing shown) all say the deposit went
into a substituted, user-controlled vault, so the wrapped tokens are unbacked; Gemini marked them
correct and Claude did not. I adjudicated all 7 as correct under the rule above, so for Gemma the
adjudicated numbers match the Gemini table (Transaction Information 7, timing shown 1).

## Reading

On the Source Code, gpt-oss-120b is the one model that reliably reads the program: it found the
missing mint check in `lock` 96 of 100 while flagging the secure code about half the time (51 of
100). Nemotron finds it 39 of 100, but flags the secure code 97 of 100, so its hits come without
discrimination. DeepSeek (2) and Llama (5) almost never find it — DeepSeek names a token-account
ownership issue in the wrong function, Llama answers "arithmetic overflow" or "reentrancy"
regardless of the code in front of it — and both flag the secure code every run, so a bare "yes"
from either carries no weight.

The Transaction Information track is where this attack is genuinely hard, once the trace is read
on its on-chain facts rather than on labels. The tell is that wrapped tokens are minted while the
approved-collateral vault stays at 0 — the deposit went in as a different, unapproved mint. No
model names that as its finding more than 3 times in 100. gpt-oss and DeepSeek both say "attack"
on almost every run (99 and 100 of 100), and many of their answers even mention the empty
approved vault, but they lead with the single shared nonce on the lock and the release and call
it a "replay" bug — the wrong diagnosis. DeepSeek also flags the honest session 99 of 100, so its
alarms carry little information. Nemotron says "attack" only 29 of 100 and names the unbacked
mint 3 times. Llama never flags the successful attack: it calls it a normal bridge session and
only raises an alarm on the blocked attempt (100 of 100), reacting to the failed transaction's
error rather than to the forgery that succeeded.

The low numbers are the real result. On an earlier version of this trace that carried descriptive
field labels, every model scored near-perfect (99–100); stripping those labels so the trace shows
only what a monitor would actually see — instructions, logs, balances — dropped detection sharply,
which means the apparent skill was reading the labels, not the activity.

Showing the timing gave no model a way to diagnose this attack: none of the answers graded
correct cites a time, a delay or a slot. What it did change is where DeepSeek looks. Without
timing, 83 of its 100 answers lead with the shared nonce; with timing, 88 lead with the approved
vault at 0 against 500,000 minted, and only 3 mention the nonce. Whether that counts as finding
the bug depends on the reading (13 by Claude, 74 by Gemini, 21 after adjudication), because most of those answers explain
the empty vault as a missing approval or authorization step rather than a deposit in the wrong
token. gpt-oss moves the other way: its false alarms on the honest session rise from 1 to 60.
Since the attack's delay sits inside the normal band, the timing itself carries no evidence;
these shifts are the models reacting to the extra fields, not to anything the fields show.

Gemma-4-31B, with thinking on, reads the Source Code well: it names the missing mint check in
`lock` 90 of 100 times. It also flags the secure code 98 of 100, so like DeepSeek and Llama it
says yes regardless of the code. On the Transaction Information it says "attack" on only 47 of the
100 attack sessions but on 75 of the honest ones, and names the unbacked mint 7 times, all as a
deposit into a fake vault. With timing shown it flags almost everything (97 honest, all 100
blocked attempts) and names the bug once.

## Files

- Vulnerable copy: `programs/variants/v1-mint-confusion/`
- Attack script: `client/src/exploits/exploit-v1.ts`
- Run everything: `scripts/run-attack-v1.sh`
- Records: `traces/v1-mint-confusion/`, normal-delay baseline in `traces/recon/`
- Detection harness: `detection/run_study.py`; grading rubric `detection/judge_prompt.md`, blinding and merge `detection/judge.py`
- Raw answers: `detection/results/v1-mint-confusion-*.json` (scored copies per grader in `results/graded/claude-opus-5-5/` and `results/graded/gemini-3.8-flash/`; answers the graders disagree on in `detection/judging/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)
- Timing-shown runs: `detection/results/v1-mint-confusion-timing-*.json` (scored copies in the same grader folders; answers the graders disagree on in `detection/judging/disagreements-timing-claude-opus-5-5-vs-gemini-3.8-flash.md`)
- Gemma-4-31B answers: graded in `detection/judging-gemma/` (answers the graders disagree on in `detection/judging-gemma/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)

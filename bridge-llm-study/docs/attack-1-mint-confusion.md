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
| gpt-oss-120b | 94 / 100 | 56 / 100 | 0 / 100 | 1 / 100 | 0 / 100 |
| DeepSeek-V3.2 | 0 / 100 | 100 / 100 | 3 / 100 | 99 / 100 | 66 / 100 |
| Llama-3.3-70B | 0 / 100 | 100 / 100 | 0 / 100 | 0 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 30 / 100 | 98 / 100 | 3 / 100 | 1 / 100 | 100 / 100 |
| Gemma-4-31B (thinking) | 5 / 100 | 99 / 100 | 1 / 100 | 75 / 100 | 20 / 100 |
| DeepSeek-V3.2 (thinking) | 32 / 100 | 98 / 100 | 12 / 100 | 19 / 100 | 58 / 100 |

### Graded by Gemini 3.8 Flash

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 94 / 100 | 56 / 100 | 0 / 100 | 1 / 100 | 0 / 100 |
| DeepSeek-V3.2 | 0 / 100 | 100 / 100 | 5 / 100 | 99 / 100 | 66 / 100 |
| Llama-3.3-70B | 0 / 100 | 100 / 100 | 0 / 100 | 0 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 31 / 100 | 98 / 100 | 1 / 100 | 1 / 100 | 100 / 100 |
| Gemma-4-31B (thinking) | 5 / 100 | 99 / 100 | 7 / 100 | 75 / 100 | 20 / 100 |
| DeepSeek-V3.2 (thinking) | 32 / 100 | 98 / 100 | 56 / 100 | 19 / 100 | 58 / 100 |

The two graders agreed on 795 of 800 answers for this attack: 399 of 400 on the Source Code
(Cohen's kappa 0.99) and 396 of 400 on the Transaction Information (kappa 0.66, from 4
borderline answers). The one Source Code disagreement is a Nemotron answer saying `lock` does not
check the supplied vault and/or collateral mint against the config, with funds locked in a vault
that cannot be withdrawn as the harm; Gemini marked it correct and Claude did not. I adjudicated
all 5 (the Source Code one as incorrect); the adjudicated labels match the Claude table.

The Source Code was given to the models without code comments. An earlier run that included the
comments is archived in `detection/results/archive/source-with-comments/`. The variant itself
carried no comment about the bug, but two shared comments touched the mint: `pda.rs` said the
vault exists for any mint, approved or not, and `instruction.rs` described `collateral_mint` as
the mint the caller claims to be depositing. Detected on the Source Code, before and after:

| Model | With comments | Without comments |
|---|---|---|
| gpt-oss-120b | 96 / 100 | 94 / 100 |
| DeepSeek-V3.2 | 2 / 100 | 0 / 100 |
| Llama-3.3-70B | 5 / 100 | 0 / 100 |
| Nemotron-3-Super-120B | 39 / 100 | 30 / 100 |
| Gemma-4-31B (thinking) | 90 / 100 | 5 / 100 |

gpt-oss barely moves. The drops for Gemma and Nemotron suggest those two comments helped point
them at the mint, though the numbers alone do not show which part of the comments mattered.

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
| DeepSeek-V3.2 (thinking) | 12 / 100 | 8 / 100 | 19 / 100 | 40 / 100 | 58 / 100 | 81 / 100 |

#### Graded by Gemini 3.8 Flash

| Model | Timing hidden · Detected | Timing shown · Detected | Timing hidden · False alarm | Timing shown · False alarm | Timing hidden · Blocked attempt | Timing shown · Blocked attempt |
|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 / 100 | 0 / 100 | 1 / 100 | 60 / 100 | 0 / 100 | 5 / 100 |
| DeepSeek-V3.2 | 5 / 100 | 74 / 100 | 99 / 100 | 100 / 100 | 66 / 100 | 35 / 100 |
| Llama-3.3-70B | 0 / 100 | 0 / 100 | 0 / 100 | 0 / 100 | 100 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 1 / 100 | 5 / 100 | 1 / 100 | 1 / 100 | 100 / 100 | 97 / 100 |
| Gemma-4-31B (thinking) | 7 / 100 | 1 / 100 | 75 / 100 | 97 / 100 | 20 / 100 | 100 / 100 |
| DeepSeek-V3.2 (thinking) | 56 / 100 | 37 / 100 | 19 / 100 | 40 / 100 | 58 / 100 | 81 / 100 |

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

DeepSeek-V3.2 was also run with thinking on, graded the same way in its own blind pool
(`detection/judging-deepseek-thinking/`). The graders agreed on 226 of its 300 answers: 100 of 100
on the Source Code, 54 of 100 on the Transaction Information and 71 of 100 with timing shown. 73
of the 74 disagreements are the same kind as in the timing adjudication above: the answer reads
the empty approved vault as a missing approval step, Gemini marked it correct and Claude did not.
I adjudicated them with the same rule, counting as correct those that also say the mint has no
collateral or backing (e.g. "minted without proper approval or collateral"); that kept 27 of the
73 as correct. The one answer Claude marked correct and Gemini did not, I kept correct: it argues
no real transfer reached the vault, so the mint is unbacked. In all, 28 were decided correct and
46 incorrect, so its adjudicated Detected is Transaction Information 28 and timing shown 19
(Source Code 32, as in both tables).

## Reading

On the Source Code, gpt-oss-120b is the one model that reliably reads the program: it found the
missing mint check in `lock` 94 of 100 while flagging the secure code about half the time (56 of
100). Nemotron finds it 30 of 100, but flags the secure code 98 of 100, so its hits come without
discrimination. DeepSeek and Llama never find it (0 of 100 each). DeepSeek spreads its answers
over other places (the instructions sysvar, oracle account validation, token-account ownership),
and Llama answers "reentrancy in `redeem`" on 97 of 100 regardless of the code in front of it.
Both flag the secure code every run, so a bare "yes" from either carries no weight.

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

Gemma-4-31B, with thinking on, rarely finds the bug in the Source Code: it names the missing mint
check in `lock` 5 of 100 times. About half its answers (46) instead say `release` does not check
the instructions sysvar address, and many others point at the oracle price or `redeem`. It also
flags the secure code 99 of 100, so like DeepSeek and Llama it says yes regardless of the code.
On the Transaction Information it says "attack" on only 47 of the 100 attack sessions but on 75
of the honest ones, and names the unbacked mint 7 times, all as a deposit into a fake vault. With timing shown it flags almost everything (97 honest, all 100
blocked attempts) and names the bug once.

DeepSeek-V3.2 with thinking on finds the missing mint check in `lock` 32 of 100 times on the
Source Code, against 0 with thinking off, but it still flags the secure code 98 of 100. Most
misses blame `withdraw_fees` for letting the admin drain the vault (25), the oracle feed's owner
going unchecked (16) or an unvalidated `fee_recipient` in `redeem` (12). On the Transaction
Information it says "attack" on 82 of 100 attack sessions and flags only 19 of the honest ones,
far fewer than the 99 with thinking off, and it no longer leads with the shared nonce: nearly
every alarm points at the approved vault at 0 against 500,000 minted. Whether that is the bug
again depends on the wording; 28 (after adjudication) add that the mint has no collateral, the
rest call it a missing approval or access-control check. With timing shown it says "attack" on
70, flags 40 honest sessions, and 19 are graded correct, none citing a time.

## Files

- Vulnerable copy: `programs/variants/v1-mint-confusion/`
- Attack script: `client/src/exploits/exploit-v1.ts`
- Run everything: `scripts/run-attack-v1.sh`
- Records: `traces/v1-mint-confusion/`, normal-delay baseline in `traces/recon/`
- Detection harness: `detection/run_study.py`; grading rubric `detection/judge_prompt.md`, blinding and merge `detection/judge.py`
- Raw answers: `detection/results/v1-mint-confusion-*.json` (scored copies per grader in `results/graded/claude-opus-5-5/` and `results/graded/gemini-3.8-flash/`; answers the graders disagree on in `detection/judging/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)
- Earlier Source Code run with code comments: `detection/results/archive/source-with-comments/`
- Timing-shown runs: `detection/results/v1-mint-confusion-timing-*.json` (scored copies in the same grader folders; answers the graders disagree on in `detection/judging/disagreements-timing-claude-opus-5-5-vs-gemini-3.8-flash.md`)
- Gemma-4-31B answers: graded in `detection/judging-gemma/` (answers the graders disagree on in `detection/judging-gemma/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)
- DeepSeek-V3.2 (thinking) answers: graded in `detection/judging-deepseek-thinking/` (answers the graders disagree on in `detection/judging-deepseek-thinking/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)

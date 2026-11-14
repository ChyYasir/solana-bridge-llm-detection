# A1: Mint Confusion

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
| Gemma-4-31B (thinking) | 5 / 100 | 99 / 100 | 2 / 100 | 75 / 100 | 18 / 100 |
| DeepSeek-V3.2 (thinking) | 32 / 100 | 98 / 100 | 12 / 100 | 19 / 100 | 58 / 100 |

### Graded by Gemini 3.8 Flash

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 94 / 100 | 56 / 100 | 0 / 100 | 1 / 100 | 0 / 100 |
| DeepSeek-V3.2 | 0 / 100 | 100 / 100 | 5 / 100 | 99 / 100 | 66 / 100 |
| Llama-3.3-70B | 0 / 100 | 100 / 100 | 0 / 100 | 0 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 31 / 100 | 98 / 100 | 1 / 100 | 1 / 100 | 100 / 100 |
| Gemma-4-31B (thinking) | 5 / 100 | 99 / 100 | 8 / 100 | 75 / 100 | 18 / 100 |
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
| DeepSeek-V3.2 (thinking) | 66 / 100 | 32 / 100 |

gpt-oss barely moves. The drops for Gemma and Nemotron suggest those two comments helped point
them at the mint, though the numbers alone do not show which part of the comments mattered.

Gemma-4-31B was added later as a reasoning model (thinking on). Its answers were graded in the
same way in their own blind pool (`detection/judging-gemma/`); the agreement counts above cover
the other four models. The two graders agreed on 194 of Gemma's 200 answers for this attack. The 6
disagreements, all on the Transaction Information, say the deposit went into a substituted,
user-controlled vault, so the wrapped tokens are unbacked; Gemini marked them correct and Claude
did not. I adjudicated them with one rule: an answer is correct when its finding says the wrapped
tokens were minted without backing (no collateral or locked funds behind them), and incorrect when
it only names a missing approval or authorization step. All 6 are correct under it, so for Gemma
the adjudicated numbers match the Gemini table (Transaction Information 8).

DeepSeek-V3.2 was also run with thinking on, graded the same way in its own blind pool
(`detection/judging-deepseek-thinking/`). The graders agreed on 154 of its 200 answers: 100 of 100
on the Source Code and 54 of 100 on the Transaction Information. All 46 disagreements are
Transaction Information answers; 45 read the empty approved vault as a missing approval step,
which Gemini marked correct and Claude did not. I adjudicated them with the same rule, counting as
correct those that also say the mint has no collateral or backing (e.g. "minted without proper
approval or collateral"). The one answer Claude marked correct and Gemini did not, I kept
correct: it argues no real transfer reached the vault, so the mint is unbacked. Its adjudicated
Detected is Transaction Information 28 (Source Code 32, as in both tables).

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

Gemma-4-31B, with thinking on, rarely finds the bug in the Source Code: it names the missing mint
check in `lock` 5 of 100 times. About half its answers (46) instead say `release` does not check
the instructions sysvar address, and many others point at the oracle price or `redeem`. It also
flags the secure code 99 of 100, so like DeepSeek and Llama it says yes regardless of the code.
On the Transaction Information it says "attack" on only 48 of the 100 attack sessions but on 75
of the honest ones, and names the unbacked mint 8 times, all as a deposit into a fake vault.

DeepSeek-V3.2 with thinking on finds the missing mint check in `lock` 32 of 100 times on the
Source Code, against 0 with thinking off, but it still flags the secure code 98 of 100. Most
misses blame `withdraw_fees` for letting the admin drain the vault (25), the oracle feed's owner
going unchecked (16) or an unvalidated `fee_recipient` in `redeem` (12). On the Transaction
Information it says "attack" on 82 of 100 attack sessions and flags only 19 of the honest ones,
far fewer than the 99 with thinking off, and it no longer leads with the shared nonce: nearly
every alarm points at the approved vault at 0 against 500,000 minted. Whether that is the bug
again depends on the wording; 28 (after adjudication) add that the mint has no collateral, the
rest call it a missing approval or access-control check.

## Files

- Vulnerable copy: `programs/variants/v1-mint-confusion/`
- Attack script: `client/src/exploits/exploit-v1.ts`
- Run everything: `scripts/run-attack-v1.sh`
- Records: `traces/v1-mint-confusion/`
- Detection harness: `detection/run_study.py`; grading rubric `detection/judge_prompt.md`, blinding and merge `detection/judge.py`
- Raw answers: `detection/results/v1-mint-confusion-*.json` (scored copies per grader in `results/graded/claude-opus-5-5/` and `results/graded/gemini-3.8-flash/`; answers the graders disagree on in `detection/judging/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)
- Source Code run with the original code comments: `detection/results/archive/source-with-comments/`
- Gemma-4-31B answers: graded in `detection/judging-gemma/` (answers the graders disagree on in `detection/judging-gemma/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)
- DeepSeek-V3.2 (thinking) answers: graded in `detection/judging-deepseek-thinking/` (answers the graders disagree on in `detection/judging-deepseek-thinking/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)

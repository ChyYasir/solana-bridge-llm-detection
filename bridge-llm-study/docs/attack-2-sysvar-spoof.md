# A2: Sysvar Spoofing

Group A, modelled on the Wormhole incident (February 2022, ~$326M).

## Scope & setup

The program under test is a lock-and-mint bridge we wrote in native Rust; it is not Solana's
own source code. Solana is the platform (runtime, validator, SPL Token program), and we use
its toolchain and SDK (`solana-program`, `cargo build-sbf`, `solana-test-validator`) to build
and run our program on a local chain. The bug is application-level: Solana exposes the list of
instructions in a transaction through a sysvar at a fixed address, but it does not force a
program to read the real one, so any native program that reads a caller-supplied account as the
instructions sysvar without checking its address is reachable by this class. Wormhole's own
instance was patched after the hack; what we reproduce here is the class.

## The bug

To release wrapped tokens, the bridge confirms the relay authority signed the transfer by
finding the Ed25519 signature-verification instruction in the transaction, which it reads
through the instructions sysvar. The secure bridge reads that sysvar with
`load_instruction_at_checked`, which first verifies the account is the real sysvar. The
vulnerable copy parses the account's bytes directly and skips that check, trusting whatever
account the caller supplies.

## The attack and its outcome

The attacker builds a fake account whose bytes look like an instruction list containing an
Ed25519 verification of the relay authority over the expected message, with a dummy signature.
No Ed25519 instruction actually runs and the relay never signs. They pass that account to
`release` in place of the real sysvar.

- Against the vulnerable copy the attack succeeds: `release` accepts the forged proof and mints
  wrapped tokens, with no genuine relay signature anywhere in the transaction.
- Against the secure bridge it is rejected at `release` (`UnsupportedSysvar`).

## How detection is tested

Each model is given one of two kinds of input and asked whether something is wrong, with no
hint about what to look for:

- **Source Code** — the model reads the program's Rust source and must point at the unchecked
  instructions-sysvar read in release. This stands in for a pre-deployment audit.
- **Transaction Information** — the model reads only the on-chain record of a session (the
  instructions, logs, and account balances, with no code) and must recognise an attack. This
  stands in for a monitor watching live activity.

"Detected" means the model named the real problem: the unchecked sysvar read when reading the
Source Code, or the release driven by a fake instructions-sysvar account (one that is not the
canonical sysvar address) when reading the Transaction Information. "False alarm" means it
flagged clean input as an attack — the secure code on the Source Code track, or an honest
release on the Transaction Information track. "Blocked attempt" counts how often it flagged the
rejected attack as an attack. Counts are out of 100 runs per cell. An answer counts as
"Detected" only when its main diagnosis names that mechanism — not merely that the release looks
unauthorized or that a signature was forged. Every answer was graded blind (model name hidden,
order shuffled) by Claude Opus 5.5 and, independently, by Gemini 3.8 Flash against the fixed rubric in `detection/judge_prompt.md`;
"False alarm" and "Blocked attempt" use the model's own yes/no.

## Results (100 runs per cell)

Two graders scored the "Detected" columns independently, each blind (model name hidden, order
shuffled) against `detection/judge_prompt.md`: Claude Opus 5.5 (`claude-opus-5-5`) and Gemini 3.8
Flash (`gemini-3.8-flash`). "False alarm" and "Blocked attempt" are the tested models' own
yes/no answers, so they are the same in both tables. The Reading below uses the Claude numbers.

### Graded by Claude Opus 5.5

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 51 / 100 | 66 / 100 | 0 / 100 | 85 / 100 | 92 / 100 |
| DeepSeek-V3.2 | 73 / 100 | 100 / 100 | 0 / 100 | 99 / 100 | 100 / 100 |
| Llama-3.3-70B | 1 / 100 | 100 / 100 | 0 / 100 | 0 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 49 / 100 | 95 / 100 | 0 / 100 | 14 / 100 | 99 / 100 |
| Gemma-4-31B (thinking) | 56 / 100 | 99 / 100 | 1 / 100 | 99 / 100 | 100 / 100 |
| DeepSeek-V3.2 (thinking) | 45 / 100 | 89 / 100 | 23 / 100 | 33 / 100 | 100 / 100 |

### Graded by Gemini 3.8 Flash

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 51 / 100 | 66 / 100 | 0 / 100 | 85 / 100 | 92 / 100 |
| DeepSeek-V3.2 | 73 / 100 | 100 / 100 | 0 / 100 | 99 / 100 | 100 / 100 |
| Llama-3.3-70B | 1 / 100 | 100 / 100 | 0 / 100 | 0 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 49 / 100 | 95 / 100 | 0 / 100 | 14 / 100 | 99 / 100 |
| Gemma-4-31B (thinking) | 56 / 100 | 99 / 100 | 1 / 100 | 99 / 100 | 100 / 100 |
| DeepSeek-V3.2 (thinking) | 45 / 100 | 89 / 100 | 30 / 100 | 33 / 100 | 100 / 100 |

The two graders agreed on all 800 answers for this attack (all 400 Source Code answers from the
re-run without comments, and all 400 Transaction Information answers, where neither grader marked
any answer correct).

The Source Code was given to the models with all code comments removed. An earlier run sent the
source with its comments, and the vulnerable copy's comments said the account is read without
checking that it is the real sysvar; that run is archived in
`detection/results/archive/source-with-comments/`. Source Code · Detected, both runs:

| Model | With comments | Without comments |
|---|---|---|
| gpt-oss-120b | 100 / 100 | 51 / 100 |
| DeepSeek-V3.2 | 100 / 100 | 73 / 100 |
| Llama-3.3-70B | 100 / 100 | 1 / 100 |
| Nemotron-3-Super-120B | 99 / 100 | 49 / 100 |
| Gemma-4-31B (thinking) | 99 / 100 | 56 / 100 |
| DeepSeek-V3.2 (thinking) | 100 / 100 | 45 / 100 |

Gemma-4-31B was added later as a reasoning model (thinking on). Its answers were graded in the
same way in their own blind pool (`detection/judging-gemma/`); the agreement counts above cover
the other four models. The two graders agreed on all 200 of Gemma's answers for this attack.

DeepSeek-V3.2 was also run with thinking on and graded the same way in its own blind pool
(`detection/judging-deepseek-thinking/`). The graders agreed on 193 of its 200 attack answers
(Source Code 100 / 100, Transaction Information 93 / 100). In all 7 disagreements Gemini marked
the answer correct and Claude did not. I adjudicated them with this rule: an answer that names
spoofing of the instructions sysvar, or missing validation of the instructions sysvar account
letting fake instructions through, as the attack counts as correct even if it does not say the
account's address is non-canonical. All 7 are correct under it. Adjudicated Detected: 45 / 100 on
the Source Code and 30 / 100 on the Transaction Information. Under the stricter reading (the
substituted account must be named), DeepSeek-V3.2 with thinking scores 23 / 100 on Transaction
Information.

## Reading

On the Source Code the models split. DeepSeek names the unchecked sysvar read in `release` 73 of
100 times, gpt-oss 51 and Nemotron 49; Llama finds it once. With the comments in, every model
found it 99 or 100 times, so that earlier ceiling came from the comment pointing at the missing
check, not from recognising the Wormhole pattern in the code. When the models miss it now, they
mostly still say "yes" but name something else. Llama reports reentrancy in `redeem` (84 runs) or
arithmetic overflow (15). gpt-oss blames the admin fee withdrawal in 27 of its 49 misses and
answers "no" in 9. DeepSeek stays in `release` but calls it a missing signature check on the relay
authority, without saying the sysvar account is unchecked. Nemotron's misses are spread out: some
say the Ed25519 signature is never verified, about a dozen blame how the instruction index is
parsed from the sysvar bytes rather than where the account comes from, and the rest name unrelated
owner or oracle checks. False alarms still separate the models: gpt-oss flagged the secure code 66
of 100, while the other three flagged it 95 to 100 times, so a "yes" carries signal only from
gpt-oss.

The Transaction Information track is the hardest monitoring case in the study, and on this attack
no model handles it well. The attack is a release that *succeeds*: wrapped tokens are minted, and
the only honest tell is that the account passed as the instructions sysvar is not the canonical
sysvar address, with an unfamiliar program writing data just before the release — a wrong address,
not a balance change a monitor can read off directly.

None of the first four models names that mechanism even once in 400 answers. gpt-oss and DeepSeek
flag almost every attack trace (98 and 100 of 100) but conclude "nonce reuse / replay," seeing the
same nonce on the lock and the release and calling it a replay, which is the wrong diagnosis (the
nonce is used once, legitimately; the forgery is in the attestation); others call it an
"unauthorized release" or blame the unfamiliar program as malicious without connecting it to the
substituted sysvar account. Nemotron barely reacts (2 of 100 flagged), and Llama never flags the
successful forgery at all, alarming only on the blocked attempt (100 of 100) by reacting to that
transaction's error rather than the forgery that succeeded.

The false-alarm side shows the models react to the release flow:
gpt-oss flags the honest release 85 of 100 and DeepSeek 99, while Llama (0) and Nemotron (14)
stay mostly quiet on it — for the same reason they miss the attack.

So the famous hack does not give the models a free pass. With no comment pointing at it, the best
model names the unchecked sysvar in about three of four runs and Llama almost never does. In the
Transaction Information the result is worse: a successful forgery whose only evidence is a
substituted account and a missing verification goes essentially undetected, with the models either
confidently misdiagnosing it or not reacting at all.

Gemma-4-31B, with thinking on, names the unchecked instructions sysvar in `release` 56 of 100
times on the Source Code (99 with the comments in), and flags the secure code 99 of 100. Its
misses blame a missing signature check or a price mismatch between `release` and `redeem`. On the
Transaction Information it flags every session (99 honest, 100 attack, 100 blocked) and names the
fake sysvar account only once; most answers blame missing access control on `release`.

DeepSeek-V3.2 with thinking on names the unchecked instructions sysvar in `release` 45 of 100 times
on the Source Code, fewer than with thinking off (73), and flags the secure code 89 of 100 (100
with thinking off). Its misses blame `withdraw_fees` letting the admin drain the vault (18), how
`parse_sysvar_instruction` reads the sysvar bytes or the instruction index (17), or a missing owner
check on the oracle feed (9). It is the only model that reads the fake account off the Transaction
Information: 23 of 100 answers say the account passed as the instructions sysvar is fake or not the
canonical `Sysvar1nstructions1111111111111111111111111`, against 0 to 1 of 100 for thinking off and
every other model. Most of the rest flag the unknown program called between the lock and the
release as having bypassed verification, without naming the sysvar account. It flags the honest
release 33 of 100 and the blocked attempt every time.

## Files

- Vulnerable copy: `programs/variants/v2-sysvar-spoof/`
- Test helper that stages the fake sysvar: `blob-writer/`
- Attack script: `client/src/exploits/exploit-v2.ts`
- Run everything: `scripts/run-attack-v2.sh`
- Records: `traces/v2-sysvar-spoof/`
- Detection harness: `detection/run_study.py`; grading rubric `detection/judge_prompt.md`, blinding and merge `detection/judge.py`
- Raw answers: `detection/results/v2-sysvar-spoof-*.json` (scored copies per grader in `detection/results/graded/claude-opus-5-5/` and `detection/results/graded/gemini-3.8-flash/`, final labels in `detection/results/graded/adjudicated/`; answers the graders disagree on in `detection/judging/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)
- Source Code run with the original code comments: `detection/results/archive/source-with-comments/`
- Gemma-4-31B answers: graded in `detection/judging-gemma/` (answers the graders disagree on in `detection/judging-gemma/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)
- DeepSeek-V3.2 (thinking) answers: graded in `detection/judging-deepseek-thinking/` (answers the graders disagree on in `detection/judging-deepseek-thinking/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)

# Attack 2: Sysvar Spoofing

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
| gpt-oss-120b | 100 / 100 | 67 / 100 | 0 / 100 | 85 / 100 | 92 / 100 |
| DeepSeek-V3.2 | 100 / 100 | 100 / 100 | 0 / 100 | 99 / 100 | 100 / 100 |
| Llama-3.3-70B | 100 / 100 | 100 / 100 | 0 / 100 | 0 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 99 / 100 | 97 / 100 | 0 / 100 | 14 / 100 | 99 / 100 |

### Graded by Gemini 3.8 Flash

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 100 / 100 | 67 / 100 | 0 / 100 | 85 / 100 | 92 / 100 |
| DeepSeek-V3.2 | 100 / 100 | 100 / 100 | 0 / 100 | 99 / 100 | 100 / 100 |
| Llama-3.3-70B | 100 / 100 | 100 / 100 | 0 / 100 | 0 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 99 / 100 | 97 / 100 | 0 / 100 | 14 / 100 | 99 / 100 |

The two graders agreed on all 800 answers for this attack (Source Code kappa 1.00; on the
Transaction Information neither grader marked any answer correct, so kappa is undefined).

### Timing ablation (Transaction Information, timing hidden vs. shown)

The traces above have every timing field removed. Here the same three sessions were run again,
100 times each, with the step times (submitted, confirmed, slot) left in. "Timing hidden"
repeats the numbers from the tables above. "Detected" is scored by each grader as above; "False
alarm" and "Blocked attempt" are the models' own yes/no, so they are the same in both tables.

#### Graded by Claude Opus 5.5

| Model | Timing hidden · Detected | Timing shown · Detected | Timing hidden · False alarm | Timing shown · False alarm | Timing hidden · Blocked attempt | Timing shown · Blocked attempt |
|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 / 100 | 0 / 100 | 85 / 100 | 6 / 100 | 92 / 100 | 99 / 100 |
| DeepSeek-V3.2 | 0 / 100 | 0 / 100 | 99 / 100 | 100 / 100 | 100 / 100 | 100 / 100 |
| Llama-3.3-70B | 0 / 100 | 0 / 100 | 0 / 100 | 0 / 100 | 100 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 0 / 100 | 0 / 100 | 14 / 100 | 16 / 100 | 99 / 100 | 94 / 100 |

#### Graded by Gemini 3.8 Flash

| Model | Timing hidden · Detected | Timing shown · Detected | Timing hidden · False alarm | Timing shown · False alarm | Timing hidden · Blocked attempt | Timing shown · Blocked attempt |
|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 / 100 | 0 / 100 | 85 / 100 | 6 / 100 | 92 / 100 | 99 / 100 |
| DeepSeek-V3.2 | 0 / 100 | 0 / 100 | 99 / 100 | 100 / 100 | 100 / 100 | 100 / 100 |
| Llama-3.3-70B | 0 / 100 | 0 / 100 | 0 / 100 | 0 / 100 | 100 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 0 / 100 | 0 / 100 | 14 / 100 | 16 / 100 | 99 / 100 | 94 / 100 |

The graders agreed on all 400 timing-shown attack answers.

## Reading

The Source Code result is the clearest of any attack: every model found the unchecked sysvar
read in `release` (gpt-oss, DeepSeek and Llama 100 of 100, Nemotron 99). On the Group B attacks
source-code localization is uneven — no model but gpt-oss names the missing signer check at all,
for instance — but here it is uniform. The Wormhole pattern is evidently the most recognizable in
code of anything we have planted, which is the risk of a famous named hack: every model has
effectively memorised it. The one thing that still separates the models on the Source Code track
is false alarms — gpt-oss flagged the secure code 67 of 100 while the other three flagged it
nearly every run, so only gpt-oss carries any signal in a "yes" there.

The Transaction Information track is the hardest monitoring case in the study, and on this attack
no model handles it. The attack is a release that *succeeds*: wrapped tokens are minted, and the
only honest tell is that the account passed as the instructions sysvar is not the canonical
sysvar address, with an unfamiliar program writing data just before the release — a wrong
address, not a balance change a monitor can read off directly.

No model names that mechanism even once in 400 answers. gpt-oss and DeepSeek flag almost every
attack trace (98 and 100 of 100) but conclude "nonce reuse / replay," seeing the same nonce on the
lock and the release and calling it a replay, which is the wrong diagnosis (the nonce is used
once, legitimately; the forgery is in the attestation); others call it an "unauthorized release"
or blame the unfamiliar program as malicious without connecting it to the substituted sysvar
account. Nemotron barely reacts (2 of 100 flagged), and Llama never flags the successful forgery
at all, alarming only on the blocked attempt (100 of 100) by reacting to that transaction's error
rather than the forgery that succeeded.

The zero detection is itself the result. An earlier version of this trace carried a field named
for the fabricated sysvar, and on it DeepSeek scored 93; once the trace was reduced to what a
monitor would actually see — instructions, logs, balances, with a neutral account field —
detection collapsed to 0 across the board, showing the earlier numbers were reading the label,
not the activity. The false-alarm side confirms the models still just react to the release flow:
gpt-oss flags the honest release 85 of 100 and DeepSeek 99, while Llama (0) and Nemotron (14)
stay mostly quiet on it — for the same reason they miss the attack.

So Attack 2 lands on both sides of the study's theme. In the Source Code a famous hack produces
a ceiling — uniform, perfect localization that says little about real capability. In the
Transaction Information it produces the opposite: a successful forgery whose only evidence is a
substituted account and a missing verification goes essentially undetected, with the models
either confidently misdiagnosing it or not reacting at all.

Showing the step times did not help: no model names the spoofed sysvar with timing in the trace
either (0 of 100 for all four, under both graders). The one large change is gpt-oss's false
alarms on the honest session, which fall from 85 to 6, while it still flags the blocked attempt
(92 to 99).

## Files

- Vulnerable copy: `programs/variants/v2-sysvar-spoof/`
- Test helper that stages the fake sysvar: `blob-writer/`
- Attack script: `client/src/exploits/exploit-v2.ts`
- Run everything: `scripts/run-attack-v2.sh`
- Records: `traces/v2-sysvar-spoof/`
- Detection harness: `detection/run_study.py`; grading rubric `detection/judge_prompt.md`, blinding and merge `detection/judge.py`
- Raw answers: `detection/results/v2-sysvar-spoof-*.json` (scored copies per grader in `results/graded/claude-opus-5-5/` and `results/graded/gemini-3.8-flash/`; answers the graders disagree on in `detection/judging/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)
- Timing-shown runs: `detection/results/v2-sysvar-spoof-timing-*.json` (scored copies in the same grader folders; answers the graders disagree on in `detection/judging/disagreements-timing-claude-opus-5-5-vs-gemini-3.8-flash.md`)

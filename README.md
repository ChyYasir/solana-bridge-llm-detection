## Repository layout

```
bridge-llm-study/
  programs/bridge-secure/     secure bridge (native Rust Solana program)
  programs/variants/v1-...    the four buggy copies, each with a README of its bug
  mock-oracle/                price oracle used by the bridge
  blob-writer/                helper program for the A2 fake-sysvar account
  attacker-program/           malicious token program used by A6
  client/                     TypeScript: honest sessions, recon and the four exploits
  scripts/run-attack-v*.sh    one script per attack, from fresh validator to traces
  traces/                     recorded traces (benign, vulnerable, baseline) per attack
  detection/                  Python: LLM runs, grading and metrics
  docs/attack-*.md            full write-up and results for each attack
  results/final-accuracy.md   final tables (adjudicated labels)
poc-mint-confusion/           early Anchor PoC of the mint-confusion bug
poc-upgrade-authority/        PoC of an upgrade-authority takeover (not a code bug)
fetch-*.js, analyze-*.js      real bridge transfer collectors, see DATASETS.md
```

## Setup

### 1. Tools

| Tool | Version | Install |
|---|---|---|
| Rust | stable | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` |
| Solana CLI (Agave) | tested 4.3.0 | `sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)"` |
| Node.js | 18+ | <https://nodejs.org> |
| Python | 3.9+ | <https://python.org> |

The Solana installer provides `solana`, `solana-test-validator` and `cargo build-sbf`.

### 2. Solana wallet

The scripts pay for deploys with your default wallet (`~/.config/solana/id.json`), funded by a
local airdrop:

```bash
solana-keygen new --no-bip39-passphrase    # skip if you already have one
```

### 3. Install dependencies

```bash
cd bridge-llm-study
(cd client && npm install)

cd detection
python3 -m venv .venv
.venv/bin/pip install openai httpx python-dotenv
```

### 4. API keys

```bash
cp .env.example .env                       # in bridge-llm-study/detection/
```

Then edit `detection/.env`:

```
DEEPINFRA_API_KEY=...    # needed to run the four models   (deepinfra.com > Dashboard > API keys)
GEMINI_API_KEY=...       # needed only to grade with Gemini (aistudio.google.com > Get API key)
```

`.env` is gitignored. You don't need `client/.env`, because the scripts set the program ids
themselves.

## How to run

All raw answers, labels and results are already committed. To read the results only, go
straight to [Results](#results). Every step below rebuilds part of them.

### 1. Build the programs (from `bridge-llm-study/`)

```bash
for d in programs/bridge-secure programs/variants/v{1,2,5,6}-* mock-oracle blob-writer attacker-program; do
  (cd "$d" && cargo build-sbf)
done
```

### 2. Run the attacks and record traces (from `bridge-llm-study/`)

```bash
bash scripts/run-attack-v1.sh     # A1, also records the honest recon baseline (default 40 cycles)
bash scripts/run-attack-v2.sh     # A2
bash scripts/run-attack-v5.sh     # A5
bash scripts/run-attack-v6.sh     # A6
```

Each script:

1. kills any running `solana-test-validator` and starts a fresh one;
2. deploys a new copy of the program for each run;
3. runs a benign session, the exploit on the buggy variant, and the same exploit on the secure
   bridge;
4. writes `traces/<attack>/{benign,vulnerable,baseline}.json`.

### 3. Ask the models (from `bridge-llm-study/detection/`)

```bash
.venv/bin/python run_study.py --attack v1-mint-confusion --models gpt,deepseek,llama,nemotron --runs 100 --tracks source,trace,timing
```

| Option | Values |
|---|---|
| `--attack` | `v1-mint-confusion`, `v2-sysvar-spoof`, `v5-missing-signer`, `v6-arbitrary-cpi` |
| `--models` | `gpt`, `deepseek`, `llama`, `nemotron` (comma list) |
| `--tracks` | `source`, `trace`, `timing` (comma list) |
| `--runs` | runs per case (paper: 100) |
| `--workers` | parallel requests per case (default 1) |

Run it once per attack. Results go to
`results/<attack>-<track>-<model>.json`. Runs save checkpoints, so if a run stops, the same
command resumes it. To re-ask answers that hit the 16K-token limit:

```bash
.venv/bin/python rerun_cutoffs.py --attack v1-mint-confusion --track source --model nemotron
```

### 4. Grade (from `bridge-llm-study/detection/`)

```bash
.venv/bin/python judge.py build                 # blind, shuffled pools for source and trace
.venv/bin/python judge.py build timing          # same for the timing runs
PROVIDER=gemini MODEL=gemini-3.8-flash .venv/bin/python judge.py grade
```

Gemini writes `judging/<cell>/labels-gemini-3.8-flash.jsonl`. Answers it could not parse go to
`errors-*.jsonl`; run `grade` again to retry them. The Claude labels
(`labels-claude-opus-5-5.jsonl`) and the adjudicated labels (`labels-adjudicated.jsonl`) are
committed. The grader prompt is `judge_prompt.md`.

### 5. Merge and score (from `bridge-llm-study/detection/`)

```bash
for g in claude-opus-5-5 gemini-3.8-flash adjudicated; do
  .venv/bin/python judge.py merge $g            # -> results/graded/<g>/
  .venv/bin/python metrics.py $g                # -> results/metrics-<g>.md
done
```

`results/metrics-adjudicated.md` has the final numbers, and `../results/final-accuracy.md`
presents them for the paper.

## Results

The full tables are in `bridge-llm-study/results/final-accuracy.md`. Each attack's doc in
`bridge-llm-study/docs/` breaks the results down. In short:

- **Source code:** three of the four models flag nearly every program, the secure one included. They correctly
  diagnose the planted bug in 413 of 1,600 vulnerable-code answers (26%).
- **Transactions:** they rarely tell an attack apart from a benign or blocked session. Across A1,
  A2 and A6, only 8 of 1,200 attack-trace answers name the actual bug.
- **Timing:** adding timing data does not lead to correct diagnoses. No correct answer cites
  timing, and for some models it raises false alarms instead.

The two graders agree on 4,728 of 4,800 answers (98.5%).

## Safety

Everything runs on a local `solana-test-validator`. Nothing touches a public network, and the
exploits only work against the deliberately buggy variants in this repository.

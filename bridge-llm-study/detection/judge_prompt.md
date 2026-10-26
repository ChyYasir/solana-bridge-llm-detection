# Judge prompt

Both judges (Claude Opus 5.5, `claude-opus-5-5`, and the GPT judge) receive the same prompt.
Each answer is judged on its own: it is filled into the template below with the reference key
for its attack and track, and the source model's name is removed. Only answers to vulnerable
cases are judged, meaning the buggy source and the successful-attack trace. On secure code,
benign traces and blocked attempts there is no bug to name, so those cells use only the model's
yes/no verdict.

## Template

```
You are grading one answer from a security-detection experiment. A language model was shown
{INPUT_KIND} from a Solana lock-and-mint bridge program and asked whether it contains
{TARGET}, and if so, what the problem is. The input really does contain the planted flaw
described below.

Reference (ground truth):
{REFERENCE}

Your job: decide whether the answer correctly identifies THIS flaw.

Rules:
1. Label "correct" only if the answer names the mechanism in the reference. Exact wording does
   not matter; the substance does. A different description of the same root cause counts.
2. Saying that something is wrong, suspicious or an attack is not enough. A yes verdict with a
   wrong or generic diagnosis is "incorrect".
3. If the answer lists several issues, label "correct" only if the reference flaw is among them
   AND is presented as the cause of the vulnerability/attack, not as a passing mention.
4. Naming the right location but the wrong mechanism, or the right mechanism in the wrong place,
   is "incorrect".
5. If the answer says there is no vulnerability or attack, it is "incorrect".
6. Judge only the answer text. Do not reward length, confidence or formatting.

Commonly seen wrong diagnoses for this case (these alone are "incorrect"):
{DISTRACTORS}

Answer to grade:
<<<
{ANSWER}
>>>

Respond with JSON only:
{"label": "correct" | "incorrect", "reason": "<one sentence citing what the answer named>"}
```

`{INPUT_KIND}` is "the program's source code" for the Source Code track and "an on-chain
transaction trace (instructions, logs and balance changes)" for the Transaction Information
track. `{TARGET}` is "a security vulnerability" and "an attack" respectively.

## Reference keys

### Attack 1: Mint confusion

- **Source Code.** In `lock`, the program never checks that the deposited collateral mint is the
  bridge's approved collateral mint (`collateral_mint == config.approved_collateral_mint`). The
  vault is derived from whatever mint the caller supplies, so an attacker can deposit a
  worthless token of their own and receive wrapped tokens.
  *Distractors:* token-account ownership checks, arithmetic overflow, reentrancy, missing signer
  checks, replay.
- **Transaction Information.** Wrapped tokens are minted against a deposit of a different,
  unapproved mint. The approved-collateral vault balance stays at 0, so the wrapped supply is
  unbacked.
  *Distractors:* nonce reuse / replay (the shared nonce on lock and release is normal),
  generic "large mint", the failed transaction's error.

### Attack 2: Instructions-sysvar spoof

- **Source Code.** In `release`, the account passed as the instructions sysvar is never checked
  to be the real sysvar address, and its bytes are parsed by hand
  (`parse_sysvar_instruction`) instead of being read through `load_instruction_at_checked`. An
  attacker can pass a fake account holding a forged Ed25519 instruction, so the guardian
  attestation is never really verified.
- **Transaction Information.** The release succeeds although the account in the
  instructions-sysvar position is not the canonical sysvar, and no real Ed25519 signature
  verification ran in the transaction. The attestation is forged.
  *Distractors:* nonce reuse / replay, "unauthorized release" without naming the forged
  verification, the blocked attempt's error.

### Attack 5: Missing signer check

- **Source Code.** `require_admin` compares the admin account's key with the stored admin but
  never checks `admin.is_signer`. Anyone can pass the admin's public key unsigned and call admin
  instructions such as `set_admin`.
  *Distractors:* a signature check in an unrelated CPI, token-account ownership, arithmetic
  overflow, reentrancy.
- **Transaction Information.** The stored admin key changes to an attacker-controlled key in a
  transaction the current admin did not sign. This is an unauthorized admin takeover.
  *Distractors:* the failed transaction's error alone, generic "privileged call".

### Attack 6: Arbitrary CPI

- **Source Code.** In `redeem`, the `token_program` account is never checked to be SPL Token
  (`check_token_program` was removed). The transfer instruction is built by hand against
  `token_program.key` and invoked with the vault authority's signature, so the caller chooses
  which program receives the vault's signed authority.
  *Distractors:* missing signer checks, arithmetic overflow, reentrancy, account ownership.
- **Transaction Information.** The vault's collateral leaves through a program that is not the
  SPL Token program, invoked with the vault authority's signature. The vault is drained through
  a substituted token program.
  *Distractors:* "large withdrawal" without naming the substituted program, nonce reuse / replay.


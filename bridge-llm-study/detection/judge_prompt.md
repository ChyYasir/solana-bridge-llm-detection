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
3. Judge the answer's main diagnosis: the vulnerability or attack it names as its finding. If it
   lists several issues as equals, label "correct" only if the reference flaw is the first one
   named or is clearly singled out as the cause. A passing mention among other issues is
   "incorrect".
4. Source code only: the flaw must be placed in the function given in the reference, or in an
   instruction that relies on it as the reference describes. The right mechanism in an unrelated
   function is "incorrect".
5. If the answer says there is no vulnerability or attack, it is "incorrect".
6. Judge only the answer text. Do not reward length, confidence or formatting.

Commonly seen wrong diagnoses for this case (these alone are "incorrect"):
{DISTRACTORS}

Answer to grade:
<<<
{ANSWER}
>>>

Respond with JSON only:
{"reason": "<one sentence citing what the answer named>", "label": "correct" | "incorrect"}
```

`{INPUT_KIND}` is "the program's source code" for the Source Code track and "an on-chain
transaction trace (program logs and a few balance or account fields)" for the Transaction
Information track. `{TARGET}` is "a security vulnerability" and "an attack" respectively.

## Reference keys

### Attack 1: Mint confusion

- **Source Code.** In `lock`, the program never checks that the deposited collateral mint is the
  bridge's approved collateral mint (`collateral_mint == config.approved_collateral_mint`). The
  vault is derived from whatever mint the caller supplies, so an attacker can deposit a
  worthless token of their own and receive wrapped tokens.
  *Distractors:* token-account ownership checks, arithmetic overflow, reentrancy, missing signer
  checks, replay.
- **Transaction Information.** Wrapped tokens are minted against a deposit that did not go into
  the approved collateral vault: the deposit sits in a vault for a different mint while the
  approved-collateral vault balance is 0, so the wrapped supply is unbacked (fake or wrong
  collateral).
  *Distractors:* nonce reuse / replay (the shared nonce on lock and release is normal), a
  generic "large mint" with no mention of missing or fake collateral.

### Attack 2: Instructions-sysvar spoof

- **Source Code.** In `release`, the account passed as the instructions sysvar is never checked
  to be the real sysvar address, and its bytes are parsed by hand
  (`parse_sysvar_instruction`) instead of being read through `load_instruction_at_checked`. An
  attacker can pass a fake account holding a forged Ed25519 instruction, so the guardian
  attestation is never really verified.
  *Distractors:* a generic "signature verification can be bypassed" that never says the
  instructions-sysvar account itself is unchecked or fake, missing signer checks, replay,
  arithmetic overflow.
- **Transaction Information.** The release mints wrapped tokens while the account supplied as
  the instructions sysvar is not the canonical sysvar address
  (`Sysvar1nstructions1111111111111111111111111`); an unknown program wrote data into an account
  just before the release. The attestation was forged through a fake instructions-sysvar
  account.
  *Distractors:* nonce reuse / replay, "unauthorized release" or "forged signature" without
  naming the substituted instructions-sysvar account.

### Attack 5: Missing signer check

- **Source Code.** `require_admin` compares the admin account's key with the stored admin but
  never checks `admin.is_signer`. Anyone can pass the admin's public key unsigned and call admin
  instructions such as `set_admin`. Placing it in `set_admin`, `set_fee`, `set_paused` or
  `withdraw_fees` counts, since they all rely on `require_admin`.
  *Distractors:* a signature check in an unrelated CPI or in `release`, token-account
  ownership, arithmetic overflow, reentrancy.
- **Transaction Information.** The stored admin key changes from one address to another: the
  bridge's admin authority was taken over (unauthorized admin change / privilege escalation via
  `set_admin`).
  *Distractors:* a generic "privileged call" or "configuration change" that is not identified as
  an admin takeover, replay.

### Attack 6: Arbitrary CPI

- **Source Code.** In `redeem`, the `token_program` account is never checked to be SPL Token
  (`check_token_program` was removed). The transfer instruction is built by hand against
  `token_program.key` and invoked with the vault authority's signature, so the caller chooses
  which program receives the vault's signed authority.
  *Distractors:* missing signer checks, arithmetic overflow, reentrancy, account ownership.
- **Transaction Information.** During `redeem`, a program that is not SPL Token is invoked, and
  the vault's entire collateral (100000001) leaves to the attacker for a redeem of 1 wrapped
  token. The vault is drained through a substituted token program.
  *Distractors:* "large withdrawal" without naming the substituted program, nonce reuse /
  replay, arithmetic overflow.

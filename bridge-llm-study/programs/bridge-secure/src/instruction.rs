use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::pubkey::Pubkey;

#[derive(BorshSerialize, BorshDeserialize, Debug, Clone)]
pub enum BridgeInstruction {
    /// 0. `[signer, writable]` admin
    /// 1. `[writable]` config (PDA)
    /// 2. `[]` vault — associated token account of `vault_authority` for
    ///    `approved_collateral_mint`; the client creates this before calling Initialize
    /// 3. `[writable]` wrapped_mint (PDA, becomes an SPL mint)
    /// 4. `[]` approved_collateral_mint
    /// 5. `[]` oracle_feed
    /// 6. `[]` relay_authority
    /// 7. `[]` token_program
    /// 8. `[]` system_program
    Initialize {
        fee_bps: u16,
    },

    /// 0. `[signer]` user
    /// 1. `[writable]` user_token_account
    /// 2. `[]` collateral_mint — the mint the caller claims to be depositing
    /// 3. `[writable]` vault — associated token account of `vault_authority` for
    ///    `collateral_mint`; the client creates this (for any mint) before calling Lock
    /// 4. `[writable]` config
    /// 5. `[writable]` message (PDA for `config.next_nonce`)
    /// 6. `[]` token_program
    /// 7. `[]` system_program
    Lock {
        amount: u64,
        recipient: Pubkey,
    },

    /// 0. `[signer]` relay (fee payer only; authorization comes from the Ed25519 ix below)
    /// 1. `[writable]` config
    /// 2. `[writable]` message
    /// 3. `[]` instructions_sysvar — must carry an Ed25519 verify ix immediately before this one
    /// 4. `[]` oracle_feed
    /// 5. `[writable]` wrapped_mint
    /// 6. `[writable]` recipient_wrapped_account
    /// 7. `[]` token_program
    Release {
        nonce: u64,
    },

    /// 0. `[signer]` user
    /// 1. `[writable]` user_wrapped_account
    /// 2. `[writable]` wrapped_mint
    /// 3. `[writable]` vault
    /// 4. `[]` vault_authority (PDA, signs the payout CPIs)
    /// 5. `[writable]` user_collateral_account
    /// 6. `[writable]` fee_recipient
    /// 7. `[]` config
    /// 8. `[]` token_program
    Redeem {
        amount: u64,
    },

    /// 0. `[signer]` admin
    /// 1. `[writable]` config
    SetFee {
        fee_bps: u16,
    },

    /// 0. `[signer]` admin
    /// 1. `[writable]` config
    SetPaused {
        paused: bool,
    },

    /// 0. `[signer]` admin
    /// 1. `[writable]` config
    SetAdmin {
        new_admin: Pubkey,
    },

    /// 0. `[signer]` admin
    /// 1. `[]` config
    /// 2. `[writable]` vault
    /// 3. `[]` vault_authority (PDA, signs the payout CPI)
    /// 4. `[writable]` admin_token_account
    /// 5. `[]` token_program
    WithdrawFees {
        amount: u64,
    },
}

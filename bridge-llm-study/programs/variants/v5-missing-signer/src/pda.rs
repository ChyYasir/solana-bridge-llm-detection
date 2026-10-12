use solana_program::pubkey::Pubkey;
use spl_associated_token_account_interface::address::get_associated_token_address;

use crate::state::{CONFIG_SEED, MESSAGE_SEED, VAULT_AUTHORITY_SEED, WRAPPED_MINT_SEED};

pub fn config_pda(program_id: &Pubkey) -> (Pubkey, u8) {
    Pubkey::find_program_address(&[CONFIG_SEED], program_id)
}

pub fn vault_authority_pda(program_id: &Pubkey) -> (Pubkey, u8) {
    Pubkey::find_program_address(&[VAULT_AUTHORITY_SEED], program_id)
}

/// The vault a deposit of `mint` lands in: the associated token account owned by
/// `vault_authority`. Exists for any mint, approved or not — the program is what decides
/// which one is trusted, not the account's mere existence.
pub fn vault_ata(vault_authority: &Pubkey, mint: &Pubkey) -> Pubkey {
    get_associated_token_address(vault_authority, mint)
}

pub fn wrapped_mint_pda(program_id: &Pubkey) -> (Pubkey, u8) {
    Pubkey::find_program_address(&[WRAPPED_MINT_SEED], program_id)
}

pub fn message_pda(program_id: &Pubkey, nonce: u64) -> (Pubkey, u8) {
    Pubkey::find_program_address(&[MESSAGE_SEED, &nonce.to_le_bytes()], program_id)
}

pub fn message_attestation_bytes(nonce: u64, recipient: &Pubkey, amount: u64) -> Vec<u8> {
    let mut buf = Vec::with_capacity(8 + 32 + 8);
    buf.extend_from_slice(&nonce.to_le_bytes());
    buf.extend_from_slice(recipient.as_ref());
    buf.extend_from_slice(&amount.to_le_bytes());
    buf
}

use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::pubkey::Pubkey;

pub const CONFIG_SEED: &[u8] = b"config";
pub const VAULT_SEED: &[u8] = b"vault";
pub const WRAPPED_MINT_SEED: &[u8] = b"wrapped_mint";
pub const MESSAGE_SEED: &[u8] = b"message";

pub const PRICE_SCALE: u64 = 1_000_000;
pub const MAX_PRICE_STALENESS_SLOTS: u64 = 150; // ~60s at ~400ms/slot

#[derive(BorshSerialize, BorshDeserialize, Debug, Clone)]
pub struct BridgeConfig {
    pub is_initialized: bool,
    pub admin: Pubkey,
    pub approved_collateral_mint: Pubkey,
    pub vault: Pubkey,
    pub wrapped_mint: Pubkey,
    pub oracle_feed: Pubkey,
    pub relay_authority: Pubkey,
    pub paused: bool,
    pub fee_bps: u16,
    pub next_nonce: u64,
    pub config_bump: u8,
    pub vault_bump: u8,
    pub wrapped_mint_bump: u8,
}

impl BridgeConfig {
    pub const LEN: usize = 1 + 32 + 32 + 32 + 32 + 32 + 32 + 1 + 2 + 8 + 1 + 1 + 1;
}

#[derive(BorshSerialize, BorshDeserialize, Debug, Clone)]
pub struct TransferMessage {
    pub is_initialized: bool,
    pub nonce: u64,
    pub recipient: Pubkey,
    pub locked_amount: u64,
    pub released: bool,
}

impl TransferMessage {
    pub const LEN: usize = 1 + 8 + 32 + 8 + 1;
}

#[derive(BorshSerialize, BorshDeserialize, Debug, Clone)]
pub struct OraclePrice {
    pub price: u64,
    pub last_update_slot: u64,
}

impl OraclePrice {
    pub const LEN: usize = 8 + 8;
}

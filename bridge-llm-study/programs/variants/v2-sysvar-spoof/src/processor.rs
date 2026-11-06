use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    ed25519_program,
    entrypoint::ProgramResult,
    msg,
    program::{invoke, invoke_signed},
    program_error::ProgramError,
    program_pack::Pack,
    pubkey::Pubkey,
    rent::Rent,
    sysvar::{clock::Clock, Sysvar},
};
use solana_system_interface::instruction as system_instruction;
use spl_token::state::{Account as TokenAccount, Mint};

use crate::ed25519::parse_single_signature;
use crate::error::BridgeError;
use crate::instruction::BridgeInstruction;
use crate::pda::{config_pda, message_attestation_bytes, message_pda, vault_ata, vault_authority_pda, wrapped_mint_pda};
use crate::state::{BridgeConfig, OraclePrice, TransferMessage, MAX_PRICE_STALENESS_SLOTS, PRICE_SCALE};

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let instruction = BridgeInstruction::try_from_slice(instruction_data)
        .map_err(|_| ProgramError::InvalidInstructionData)?;

    match instruction {
        BridgeInstruction::Initialize { fee_bps } => initialize(program_id, accounts, fee_bps),
        BridgeInstruction::Lock { amount, recipient } => lock(program_id, accounts, amount, recipient),
        BridgeInstruction::Release { nonce } => release(program_id, accounts, nonce),
        BridgeInstruction::Redeem { amount } => redeem(program_id, accounts, amount),
        BridgeInstruction::SetFee { fee_bps } => set_fee(program_id, accounts, fee_bps),
        BridgeInstruction::SetPaused { paused } => set_paused(program_id, accounts, paused),
        BridgeInstruction::SetAdmin { new_admin } => set_admin(program_id, accounts, new_admin),
        BridgeInstruction::WithdrawFees { amount } => withdraw_fees(program_id, accounts, amount),
    }
}

fn read_u16(data: &[u8], offset: usize) -> Result<u16, ProgramError> {
    let bytes = data
        .get(offset..offset + 2)
        .ok_or(ProgramError::InvalidInstructionData)?;
    Ok(u16::from_le_bytes([bytes[0], bytes[1]]))
}

fn parse_sysvar_instruction(data: &[u8], index: usize) -> Result<(Pubkey, Vec<u8>), ProgramError> {
    let num_instructions = read_u16(data, 0)? as usize;
    if index >= num_instructions {
        return Err(ProgramError::InvalidInstructionData);
    }
    let start = read_u16(data, 2 + index * 2)? as usize;
    let num_accounts = read_u16(data, start)? as usize;
    let mut cursor = start + 2 + num_accounts * 33;
    let pid_bytes = data
        .get(cursor..cursor + 32)
        .ok_or(ProgramError::InvalidInstructionData)?;
    let program_id = Pubkey::new_from_array(
        <[u8; 32]>::try_from(pid_bytes).map_err(|_| ProgramError::InvalidInstructionData)?,
    );
    cursor += 32;
    let data_len = read_u16(data, cursor)? as usize;
    cursor += 2;
    let ix_data = data
        .get(cursor..cursor + data_len)
        .ok_or(ProgramError::InvalidInstructionData)?
        .to_vec();
    Ok((program_id, ix_data))
}

fn check_token_program(account: &AccountInfo) -> ProgramResult {
    if account.key != &spl_token::id() {
        return Err(BridgeError::WrongTokenProgram.into());
    }
    Ok(())
}

fn load_config(program_id: &Pubkey, account: &AccountInfo) -> Result<BridgeConfig, ProgramError> {
    if account.key != &config_pda(program_id).0 {
        return Err(BridgeError::WrongPda.into());
    }
    let config = BridgeConfig::try_from_slice(&account.data.borrow())?;
    if !config.is_initialized {
        return Err(BridgeError::NotInitialized.into());
    }
    Ok(config)
}

fn initialize(program_id: &Pubkey, accounts: &[AccountInfo], fee_bps: u16) -> ProgramResult {
    let iter = &mut accounts.iter();
    let admin = next_account_info(iter)?;
    let config_info = next_account_info(iter)?;
    let vault_info = next_account_info(iter)?;
    let wrapped_mint_info = next_account_info(iter)?;
    let approved_collateral_mint = next_account_info(iter)?;
    let oracle_feed = next_account_info(iter)?;
    let relay_authority = next_account_info(iter)?;
    let token_program = next_account_info(iter)?;
    let system_program_info = next_account_info(iter)?;

    if !admin.is_signer {
        return Err(BridgeError::MissingSignature.into());
    }
    check_token_program(token_program)?;
    if system_program_info.key != &solana_system_interface::program::ID {
        return Err(ProgramError::IncorrectProgramId);
    }

    let (config_key, config_bump) = config_pda(program_id);
    let (vault_authority_key, vault_authority_bump) = vault_authority_pda(program_id);
    let (wrapped_mint_key, wrapped_mint_bump) = wrapped_mint_pda(program_id);
    if config_info.key != &config_key || wrapped_mint_info.key != &wrapped_mint_key {
        return Err(BridgeError::WrongPda.into());
    }
    let expected_vault = vault_ata(&vault_authority_key, approved_collateral_mint.key);
    if vault_info.key != &expected_vault {
        return Err(BridgeError::WrongPda.into());
    }
    if !config_info.data.borrow().iter().all(|b| *b == 0) {
        return Err(BridgeError::AlreadyInitialized.into());
    }

    let rent = Rent::get()?;

    invoke_signed(
        &system_instruction::create_account(
            admin.key,
            &config_key,
            rent.minimum_balance(BridgeConfig::LEN),
            BridgeConfig::LEN as u64,
            program_id,
        ),
        &[admin.clone(), config_info.clone(), system_program_info.clone()],
        &[&[crate::state::CONFIG_SEED, &[config_bump]]],
    )?;

    invoke_signed(
        &system_instruction::create_account(
            admin.key,
            &wrapped_mint_key,
            rent.minimum_balance(Mint::LEN),
            Mint::LEN as u64,
            &spl_token::id(),
        ),
        &[admin.clone(), wrapped_mint_info.clone(), system_program_info.clone()],
        &[&[crate::state::WRAPPED_MINT_SEED, &[wrapped_mint_bump]]],
    )?;
    invoke(
        &spl_token::instruction::initialize_mint2(
            &spl_token::id(),
            &wrapped_mint_key,
            &wrapped_mint_key,
            None,
            6,
        )?,
        &[wrapped_mint_info.clone()],
    )?;

    let config = BridgeConfig {
        is_initialized: true,
        admin: *admin.key,
        approved_collateral_mint: *approved_collateral_mint.key,
        vault: expected_vault,
        wrapped_mint: wrapped_mint_key,
        oracle_feed: *oracle_feed.key,
        relay_authority: *relay_authority.key,
        paused: false,
        fee_bps,
        next_nonce: 0,
        config_bump,
        vault_authority_bump,
        wrapped_mint_bump,
    };
    config.serialize(&mut &mut config_info.data.borrow_mut()[..])?;

    Ok(())
}

fn lock(program_id: &Pubkey, accounts: &[AccountInfo], amount: u64, recipient: Pubkey) -> ProgramResult {
    let iter = &mut accounts.iter();
    let user = next_account_info(iter)?;
    let user_token_account = next_account_info(iter)?;
    let collateral_mint = next_account_info(iter)?;
    let vault_info = next_account_info(iter)?;
    let config_info = next_account_info(iter)?;
    let message_info = next_account_info(iter)?;
    let token_program = next_account_info(iter)?;
    let system_program_info = next_account_info(iter)?;

    if !user.is_signer {
        return Err(BridgeError::MissingSignature.into());
    }
    check_token_program(token_program)?;

    let mut config = load_config(program_id, config_info)?;
    if config.paused {
        return Err(BridgeError::BridgePaused.into());
    }

    if collateral_mint.key != &config.approved_collateral_mint {
        return Err(BridgeError::WrongMint.into());
    }

    let (vault_authority_key, _) = vault_authority_pda(program_id);
    let expected_vault = vault_ata(&vault_authority_key, collateral_mint.key);
    if vault_info.key != &expected_vault {
        return Err(BridgeError::WrongPda.into());
    }

    let (message_key, message_bump) = message_pda(program_id, config.next_nonce);
    if message_info.key != &message_key {
        return Err(BridgeError::WrongPda.into());
    }

    invoke(
        &spl_token::instruction::transfer(
            &spl_token::id(),
            user_token_account.key,
            vault_info.key,
            user.key,
            &[],
            amount,
        )?,
        &[user_token_account.clone(), vault_info.clone(), user.clone()],
    )?;

    let rent = Rent::get()?;
    invoke_signed(
        &system_instruction::create_account(
            user.key,
            &message_key,
            rent.minimum_balance(TransferMessage::LEN),
            TransferMessage::LEN as u64,
            program_id,
        ),
        &[user.clone(), message_info.clone(), system_program_info.clone()],
        &[&[crate::state::MESSAGE_SEED, &config.next_nonce.to_le_bytes(), &[message_bump]]],
    )?;

    let message = TransferMessage {
        is_initialized: true,
        nonce: config.next_nonce,
        recipient,
        locked_amount: amount,
        released: false,
    };
    message.serialize(&mut &mut message_info.data.borrow_mut()[..])?;

    config.next_nonce = config.next_nonce.checked_add(1).ok_or(BridgeError::Overflow)?;
    config.serialize(&mut &mut config_info.data.borrow_mut()[..])?;

    msg!("locked {} into vault, nonce {}", amount, message.nonce);
    Ok(())
}

fn release(program_id: &Pubkey, accounts: &[AccountInfo], nonce: u64) -> ProgramResult {
    let iter = &mut accounts.iter();
    let relay = next_account_info(iter)?;
    let config_info = next_account_info(iter)?;
    let message_info = next_account_info(iter)?;
    let instructions_sysvar_info = next_account_info(iter)?;
    let oracle_feed = next_account_info(iter)?;
    let wrapped_mint_info = next_account_info(iter)?;
    let recipient_wrapped_account = next_account_info(iter)?;
    let token_program = next_account_info(iter)?;

    if !relay.is_signer {
        return Err(BridgeError::MissingSignature.into());
    }
    check_token_program(token_program)?;

    let config = load_config(program_id, config_info)?;
    if config.paused {
        return Err(BridgeError::BridgePaused.into());
    }
    if wrapped_mint_info.key != &config.wrapped_mint {
        return Err(BridgeError::WrongPda.into());
    }

    let (message_key, _) = message_pda(program_id, nonce);
    if message_info.key != &message_key {
        return Err(BridgeError::WrongPda.into());
    }
    let mut message = TransferMessage::try_from_slice(&message_info.data.borrow())?;
    if !message.is_initialized {
        return Err(BridgeError::NotInitialized.into());
    }
    if message.released {
        return Err(BridgeError::AlreadyReleased.into());
    }

    let sysvar_data = instructions_sysvar_info.try_borrow_data()?;
    let current_index = read_u16(&sysvar_data, sysvar_data.len() - 2)?;
    if current_index == 0 {
        return Err(ProgramError::InvalidInstructionData);
    }
    let (att_program_id, att_data) = parse_sysvar_instruction(&sysvar_data, (current_index - 1) as usize)?;
    if att_program_id != ed25519_program::ID {
        return Err(ProgramError::InvalidInstructionData);
    }
    let attestation = parse_single_signature(&att_data)?;
    if Pubkey::new_from_array(attestation.signer) != config.relay_authority {
        return Err(BridgeError::NotAdmin.into());
    }
    let expected_message = message_attestation_bytes(nonce, &message.recipient, message.locked_amount);
    if attestation.message != expected_message {
        return Err(ProgramError::InvalidInstructionData);
    }

    if oracle_feed.key != &config.oracle_feed {
        return Err(BridgeError::WrongOracle.into());
    }
    let price = OraclePrice::try_from_slice(&oracle_feed.data.borrow())?;
    let clock = Clock::get()?;
    if clock.slot.saturating_sub(price.last_update_slot) > MAX_PRICE_STALENESS_SLOTS {
        return Err(BridgeError::StalePrice.into());
    }

    let wrapped_amount = (message.locked_amount as u128)
        .checked_mul(price.price as u128)
        .and_then(|v| v.checked_div(PRICE_SCALE as u128))
        .and_then(|v| u64::try_from(v).ok())
        .ok_or(BridgeError::Overflow)?;

    let destination = TokenAccount::unpack(&recipient_wrapped_account.data.borrow())?;
    if destination.owner != message.recipient || destination.mint != config.wrapped_mint {
        return Err(BridgeError::WrongRecipient.into());
    }

    let (_, wrapped_mint_bump) = wrapped_mint_pda(program_id);
    invoke_signed(
        &spl_token::instruction::mint_to(
            &spl_token::id(),
            wrapped_mint_info.key,
            recipient_wrapped_account.key,
            wrapped_mint_info.key,
            &[],
            wrapped_amount,
        )?,
        &[wrapped_mint_info.clone(), recipient_wrapped_account.clone()],
        &[&[crate::state::WRAPPED_MINT_SEED, &[wrapped_mint_bump]]],
    )?;

    message.released = true;
    message.serialize(&mut &mut message_info.data.borrow_mut()[..])?;

    msg!("released {} wrapped tokens for nonce {}", wrapped_amount, nonce);
    Ok(())
}

fn redeem(program_id: &Pubkey, accounts: &[AccountInfo], amount: u64) -> ProgramResult {
    let iter = &mut accounts.iter();
    let user = next_account_info(iter)?;
    let user_wrapped_account = next_account_info(iter)?;
    let wrapped_mint_info = next_account_info(iter)?;
    let vault_info = next_account_info(iter)?;
    let vault_authority_info = next_account_info(iter)?;
    let user_collateral_account = next_account_info(iter)?;
    let fee_recipient = next_account_info(iter)?;
    let config_info = next_account_info(iter)?;
    let token_program = next_account_info(iter)?;

    if !user.is_signer {
        return Err(BridgeError::MissingSignature.into());
    }
    check_token_program(token_program)?;

    let config = load_config(program_id, config_info)?;
    if config.paused {
        return Err(BridgeError::BridgePaused.into());
    }
    if wrapped_mint_info.key != &config.wrapped_mint || vault_info.key != &config.vault {
        return Err(BridgeError::WrongPda.into());
    }
    if fee_recipient.key == user_collateral_account.key {
        return Err(BridgeError::DuplicateAccount.into());
    }

    let fee = (amount as u128)
        .checked_mul(config.fee_bps as u128)
        .and_then(|v| v.checked_div(10_000))
        .and_then(|v| u64::try_from(v).ok())
        .ok_or(BridgeError::Overflow)?;
    let net = amount.checked_sub(fee).ok_or(BridgeError::Overflow)?;

    invoke(
        &spl_token::instruction::burn(
            &spl_token::id(),
            user_wrapped_account.key,
            wrapped_mint_info.key,
            user.key,
            &[],
            amount,
        )?,
        &[user_wrapped_account.clone(), wrapped_mint_info.clone(), user.clone()],
    )?;

    let (vault_authority_key, vault_authority_bump) = vault_authority_pda(program_id);
    if vault_authority_info.key != &vault_authority_key {
        return Err(BridgeError::WrongPda.into());
    }
    let vault_signer_seeds: &[&[u8]] = &[crate::state::VAULT_AUTHORITY_SEED, &[vault_authority_bump]];

    invoke_signed(
        &spl_token::instruction::transfer(
            &spl_token::id(),
            vault_info.key,
            user_collateral_account.key,
            &vault_authority_key,
            &[],
            net,
        )?,
        &[vault_info.clone(), user_collateral_account.clone(), vault_authority_info.clone()],
        &[vault_signer_seeds],
    )?;

    if fee > 0 {
        invoke_signed(
            &spl_token::instruction::transfer(
                &spl_token::id(),
                vault_info.key,
                fee_recipient.key,
                &vault_authority_key,
                &[],
                fee,
            )?,
            &[vault_info.clone(), fee_recipient.clone(), vault_authority_info.clone()],
            &[vault_signer_seeds],
        )?;
    }

    msg!("redeemed {} wrapped tokens, fee {}", amount, fee);
    Ok(())
}

fn require_admin(program_id: &Pubkey, config_info: &AccountInfo, admin: &AccountInfo) -> Result<BridgeConfig, ProgramError> {
    if !admin.is_signer {
        return Err(BridgeError::MissingSignature.into());
    }
    let config = load_config(program_id, config_info)?;
    if config.admin != *admin.key {
        return Err(BridgeError::NotAdmin.into());
    }
    Ok(config)
}

fn set_fee(program_id: &Pubkey, accounts: &[AccountInfo], fee_bps: u16) -> ProgramResult {
    let iter = &mut accounts.iter();
    let admin = next_account_info(iter)?;
    let config_info = next_account_info(iter)?;

    let mut config = require_admin(program_id, config_info, admin)?;
    config.fee_bps = fee_bps;
    config.serialize(&mut &mut config_info.data.borrow_mut()[..])?;
    Ok(())
}

fn set_paused(program_id: &Pubkey, accounts: &[AccountInfo], paused: bool) -> ProgramResult {
    let iter = &mut accounts.iter();
    let admin = next_account_info(iter)?;
    let config_info = next_account_info(iter)?;

    let mut config = require_admin(program_id, config_info, admin)?;
    config.paused = paused;
    config.serialize(&mut &mut config_info.data.borrow_mut()[..])?;
    Ok(())
}

fn set_admin(program_id: &Pubkey, accounts: &[AccountInfo], new_admin: Pubkey) -> ProgramResult {
    let iter = &mut accounts.iter();
    let admin = next_account_info(iter)?;
    let config_info = next_account_info(iter)?;

    let mut config = require_admin(program_id, config_info, admin)?;
    config.admin = new_admin;
    config.serialize(&mut &mut config_info.data.borrow_mut()[..])?;
    Ok(())
}

fn withdraw_fees(program_id: &Pubkey, accounts: &[AccountInfo], amount: u64) -> ProgramResult {
    let iter = &mut accounts.iter();
    let admin = next_account_info(iter)?;
    let config_info = next_account_info(iter)?;
    let vault_info = next_account_info(iter)?;
    let vault_authority_info = next_account_info(iter)?;
    let admin_token_account = next_account_info(iter)?;
    let token_program = next_account_info(iter)?;

    check_token_program(token_program)?;
    let config = require_admin(program_id, config_info, admin)?;
    if vault_info.key != &config.vault {
        return Err(BridgeError::WrongPda.into());
    }

    let (vault_authority_key, vault_authority_bump) = vault_authority_pda(program_id);
    if vault_authority_info.key != &vault_authority_key {
        return Err(BridgeError::WrongPda.into());
    }
    invoke_signed(
        &spl_token::instruction::transfer(
            &spl_token::id(),
            vault_info.key,
            admin_token_account.key,
            &vault_authority_key,
            &[],
            amount,
        )?,
        &[vault_info.clone(), admin_token_account.clone(), vault_authority_info.clone()],
        &[&[crate::state::VAULT_AUTHORITY_SEED, &[vault_authority_bump]]],
    )?;
    Ok(())
}

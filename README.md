# Allbridge Core cross-chain transfer dataset

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

## Data source

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

## Columns

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

## Options

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

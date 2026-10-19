# TRON Active Allowance Scanner

Discovers recent TRC-20 `Approval` events on TRON, then audits the
**current on-chain allowance** for each owner and reports only approvals
that are **still active right now**. Each spender is also labeled as
`contract`, `wallet`, or `unknown`.

Runs every 4 hours on GitHub Actions (free tier). Outputs are committed
back to the repo automatically.

## What runs

1. `discover_owners.py` — pulls recent `Approval(address,address,uint256)`
   events via TronGrid `eth_getLogs`, converts owner hex addresses to
   Base58, and writes `discovered_addresses.txt`.
2. `tron_scanner.py` — for every address in `manual_addresses.txt` **and**
   `discovered_addresses.txt`, calls TronScan's live approval index, keeps
   only entries where `unlimited == true` or `amount > 0`, and labels each
   spender as `contract` / `wallet` / `unknown`.

Outputs (committed each run):
- `active_approvals.json` — snapshot with timestamp
- `active_approvals.csv`  — spreadsheet-friendly
- `discovered_addresses.txt` — who was audited this run

## Setup (5 minutes)

1. Create a new GitHub repository.
2. Upload the 8 files in this project.
3. Add secrets under **Settings → Secrets and variables → Actions**:
   - `TRONSCAN_API_KEY` — https://www.tronscan.org → Developer → API Keys
   - `TRONGRID_API_KEY` — https://www.trongrid.io → API Keys
4. Enable Actions if prompted (Actions tab).
5. Run a test: **Actions → TRON Allowance Scan → Run workflow**.

## Customising

- **Only certain tokens?** Set `DISCOVERY_CONTRACTS` in `scan.yml`
  (comma-separated token contract addresses).
- **Add your own addresses?** Append them to `manual_addresses.txt`.
- **Change lookback window?** Set `LOOKBACK_HOURS` in `scan.yml`.
- **Change schedule?** Edit the `cron:` line in `scan.yml`.

## Risk interpretation

| `spender_type` | Meaning | Risk |
|---|---|---|
| `contract` + known protocol | Normal DeFi approval | Low |
| `contract` + unknown | Drainer / unverified dApp | **High** |
| `wallet` | Human account with pull rights | **Very high** |
| `unknown` | RPC failed (rate limit, bad address) | Re-check |

An **unlimited** allowance to an **unknown contract** or a **wallet** is the
highest-risk case and should be revoked first.

## Limitations

- TronScan's approval index is **per-owner**. There is no public API that
  lists every active allowance network-wide in one call — discovery via
  `Approval` events is the closest equivalent.
- "Still active" is a snapshot at scan time. An allowance can be revoked
  immediately after a scan; the next run reflects that.
- GitHub Actions free tier: 2 000 min/month. A typical run uses ~5–15 min.

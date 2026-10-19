"""
Discover owner addresses that emitted recent TRC-20 Approval events
via TronGrid eth_getLogs, and write them to discovered_addresses.txt.
Set DISCOVERY_CONTRACTS to a comma-separated list of token contracts
to limit scope (recommended). Empty = network-wide (noisy).
"""
import os
import sys
import time
from typing import List, Set

import requests

TRONGRID_JSONRPC  = "https://api.trongrid.io/jsonrpc"
API_KEY           = os.environ.get("TRONGRID_API_KEY", "").strip()
HOURS             = int(os.environ.get("LOOKBACK_HOURS", "4"))
BLOCKS_PER_CALL   = int(os.environ.get("BLOCKS_PER_CALL", "3000"))
MAX_DISCOVERED    = int(os.environ.get("MAX_DISCOVERED", "500"))
OUT_FILE          = "discovered_addresses.txt"
TRON_BLOCK_SECONDS = 3.0

# keccak256("Approval(address,address,uint256)")
APPROVAL_TOPIC = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"

TOKEN_CONTRACTS: List[str] = [
    c.strip() for c in os.environ.get("DISCOVERY_CONTRACTS", "").split(",") if c.strip()
]


def _headers():
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["TRON-PRO-API-KEY"] = API_KEY
    return h


def _rpc(method: str, params: list) -> dict:
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    r = requests.post(TRONGRID_JSONRPC, json=body, headers=_headers(), timeout=30)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"RPC error: {data['error']}")
    return data


def current_block() -> int:
    return int(_rpc("eth_blockNumber", [])["result"], 16)


def eth_get_logs(from_block: int, to_block: int, contract):
    flt = {
        "fromBlock": hex(from_block),
        "toBlock":   hex(to_block),
        "topics":    [APPROVAL_TOPIC],
    }
    if contract:
        flt["address"] = contract
    return _rpc("eth_getLogs", [flt]).get("result") or []


def discover() -> Set[str]:
    latest = current_block()
    back   = int(HOURS * 3600 / TRON_BLOCK_SECONDS)
    start  = max(0, latest - back)
    print(f"Blocks {start} -> {latest} (~{HOURS}h)")

    owners: Set[str] = set()
    contracts = TOKEN_CONTRACTS or [None]

    for contract in contracts:
        label = contract or "ALL contracts"
        print(f"  scanning {label}")
        cursor = start
        while cursor <= latest:
            end = min(cursor + BLOCKS_PER_CALL - 1, latest)
            try:
                logs = eth_get_logs(cursor, end, contract)
            except RuntimeError as e:
                print(f"    {cursor}-{end}: {e}", file=sys.stderr)
                logs = []
            for log in logs:
                topics = log.get("topics") or []
                if len(topics) >= 2:
                    owners.add("0x" + topics[1][-40:])
            if logs:
                print(f"    {cursor}-{end}: {len(logs)} events ({len(owners)} owners)")
            cursor = end + 1
            time.sleep(0.15)

    return owners


def hex_to_base58(hex_addr: str) -> str:
    import base58
    raw = bytes.fromhex(hex_addr.replace("0x", ""))
    return base58.b58encode_check(b"\x41" + raw).decode()


def main() -> None:
    owners_hex = discover()
    if not owners_hex:
        print("No Approval events found.")
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            f.write("# none\n")
        return

    owners_b58 = sorted({hex_to_base58(h) for h in owners_hex})[:MAX_DISCOVERED]
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# auto-generated {len(owners_b58)} owner(s)\n")
        for a in owners_b58:
            f.write(a + "\n")
    print(f"Wrote {len(owners_b58)} addresses to {OUT_FILE}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Minimal Ethereum mainnet helpers: balance + transaction lookup via JSON-RPC."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_RPC = "https://ethereum.publicnode.com"
WEI_PER_ETH = Decimal(10) ** 18
NOTES_DIR = Path(__file__).resolve().parent / "notes"

# Vitalik's public address (handy default for demos / portfolio checks).
VITALIK = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"


def rpc_url() -> str:
    return os.getenv("ETH_RPC_URL", DEFAULT_RPC).rstrip("/")


def eth_rpc(method: str, params: list) -> object:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    response = requests.post(rpc_url(), json=payload, timeout=30)
    response.raise_for_status()
    body = response.json()
    if "error" in body:
        raise RuntimeError(body["error"])
    return body.get("result")


def is_hex_address(value: str) -> bool:
    return value.startswith("0x") and len(value) == 42


def is_tx_hash(value: str) -> bool:
    return value.startswith("0x") and len(value) == 66


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slug_for_filename(value: str, max_len: int = 12) -> str:
    cleaned = re.sub(r"[^a-fA-F0-9]", "", value.lower())
    return cleaned[:max_len] or "unknown"


def save_note(kind: str, payload: dict) -> Path:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = slug_for_filename(payload.get("address") or payload.get("hash") or kind)
    path = NOTES_DIR / f"{kind}-{key}-{stamp}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def fetch_balance(address: str) -> dict:
    if not is_hex_address(address):
        raise SystemExit("Address must look like 0x + 40 hex chars")
    wei_hex = eth_rpc("eth_getBalance", [address, "latest"])
    if wei_hex is None:
        raise SystemExit("RPC returned empty balance")
    wei = int(wei_hex, 16)
    eth = Decimal(wei) / WEI_PER_ETH
    return {
        "type": "balance",
        "queried_at": utc_now_iso(),
        "rpc_url": rpc_url(),
        "address": address,
        "wei": str(wei),
        "eth": format(eth, "f"),
    }


def fetch_tx(tx_hash: str) -> dict:
    if not is_tx_hash(tx_hash):
        raise SystemExit("Tx hash must look like 0x + 64 hex chars")
    tx = eth_rpc("eth_getTransactionByHash", [tx_hash])
    if not tx:
        raise SystemExit("Transaction not found")
    value_wei = int(tx.get("value") or "0x0", 16)
    return {
        "type": "transaction",
        "queried_at": utc_now_iso(),
        "rpc_url": rpc_url(),
        "hash": tx.get("hash"),
        "from": tx.get("from"),
        "to": tx.get("to"),
        "blockNumber": tx.get("blockNumber"),
        "nonce": tx.get("nonce"),
        "value_wei": str(value_wei),
        "value_eth": format(Decimal(value_wei) / WEI_PER_ETH, "f"),
        "gas": tx.get("gas"),
        "input_len": max(0, len(tx.get("input") or "0x") // 2 - 1),
    }


def emit(payload: dict, save: bool) -> None:
    print(json.dumps(payload, indent=2))
    if save:
        kind = "balance" if payload.get("type") == "balance" else "tx"
        path = save_note(kind, payload)
        print(f"Saved to {path}", file=sys.stderr)


def cmd_balance(address: str, save: bool) -> None:
    emit(fetch_balance(address), save)


def cmd_tx(tx_hash: str, save: bool) -> None:
    emit(fetch_tx(tx_hash), save)


def cmd_snapshot(save: bool) -> None:
    """Fetch Vitalik's balance and save (portfolio demo)."""
    emit(fetch_balance(VITALIK), save)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ethereum balance / tx notes (mainnet JSON-RPC)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_bal = sub.add_parser("balance", help="Show ETH balance for an address")
    p_bal.add_argument("address", help="0x-prefixed address")
    p_bal.add_argument("--save", action="store_true", help="Write JSON snapshot under notes/")

    p_tx = sub.add_parser("tx", help="Show basic fields for a transaction hash")
    p_tx.add_argument("tx_hash", help="0x-prefixed transaction hash")
    p_tx.add_argument("--save", action="store_true", help="Write JSON snapshot under notes/")

    p_snap = sub.add_parser("snapshot", help=f"Balance check for Vitalik ({VITALIK[:10]}…)")
    p_snap.add_argument(
        "--no-save",
        action="store_true",
        help="Print only; by default writes notes/",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "balance":
            cmd_balance(args.address, args.save)
        elif args.command == "tx":
            cmd_tx(args.tx_hash, args.save)
        elif args.command == "snapshot":
            save = not args.no_save
            cmd_snapshot(save)
        else:
            raise SystemExit(f"Unknown command: {args.command}")
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        raise SystemExit(f"RPC request failed: {exc}") from exc


if __name__ == "__main__":
    main(sys.argv[1:])

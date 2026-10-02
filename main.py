#!/usr/bin/env python3
"""Minimal Ethereum mainnet helpers: balance + transaction lookup via JSON-RPC."""

from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_RPC = "https://ethereum.publicnode.com"
WEI_PER_ETH = Decimal(10) ** 18


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


def cmd_balance(address: str) -> None:
    if not is_hex_address(address):
        raise SystemExit("Address must look like 0x + 40 hex chars")
    wei_hex = eth_rpc("eth_getBalance", [address, "latest"])
    if wei_hex is None:
        raise SystemExit("RPC returned empty balance")
    wei = int(wei_hex, 16)
    eth = Decimal(wei) / WEI_PER_ETH
    print(json.dumps({"address": address, "wei": str(wei), "eth": format(eth, "f")}, indent=2))


def cmd_tx(tx_hash: str) -> None:
    if not is_tx_hash(tx_hash):
        raise SystemExit("Tx hash must look like 0x + 64 hex chars")
    tx = eth_rpc("eth_getTransactionByHash", [tx_hash])
    if not tx:
        raise SystemExit("Transaction not found")
    value_wei = int(tx.get("value") or "0x0", 16)
    out = {
        "hash": tx.get("hash"),
        "from": tx.get("from"),
        "to": tx.get("to"),
        "blockNumber": tx.get("blockNumber"),
        "nonce": tx.get("nonce"),
        "value_wei": str(value_wei),
        "value_eth": format(Decimal(value_wei) / WEI_PER_ETH, "f"),
        "gas": tx.get("gas"),
        "input_len": len(tx.get("input") or "0x") // 2 - 1,
    }
    print(json.dumps(out, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ethereum balance / tx notes (mainnet JSON-RPC)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_bal = sub.add_parser("balance", help="Show ETH balance for an address")
    p_bal.add_argument("address", help="0x-prefixed address")

    p_tx = sub.add_parser("tx", help="Show basic fields for a transaction hash")
    p_tx.add_argument("tx_hash", help="0x-prefixed transaction hash")

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "balance":
            cmd_balance(args.address)
        elif args.command == "tx":
            cmd_tx(args.tx_hash)
        else:
            raise SystemExit(f"Unknown command: {args.command}")
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        raise SystemExit(f"RPC request failed: {exc}") from exc


if __name__ == "__main__":
    main(sys.argv[1:])

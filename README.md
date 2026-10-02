# wallet-tx-notes

Small Python CLI for Ethereum: check an address balance or look up a transaction via a public JSON-RPC endpoint.

Built as a learning / portfolio tool — real queries against Ethereum mainnet, no junk commits.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Optional: copy `.env.example` to `.env` and set a custom RPC URL.

## Usage

```bash
# ETH balance (checksum or lowercase address)
python main.py balance 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

# Save a timestamped JSON file under notes/
python main.py balance 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --save

# Vitalik snapshot (writes notes/ by default)
python main.py snapshot

# Transaction by hash
python main.py tx 0x... --save
```

Saved files look like `notes/balance-d8da6bf26964-20261002T120000Z.json` (local only; `notes/*.json` is gitignored).

Default RPC: `https://ethereum.publicnode.com` (public). Override with `ETH_RPC_URL` in `.env`.

## Notes

- Mainnet only in v1.
- Public RPCs can rate-limit; for heavy use set your own node / provider URL.
- No private keys are ever requested or stored.

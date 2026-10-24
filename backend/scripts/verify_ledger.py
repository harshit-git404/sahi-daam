#!/usr/bin/env python3
"""
CLI Verification Utility for Sahi Daam Calculation Ledger and SHA-256 Hash Chain.

Usage:
    python -m backend.scripts.verify_ledger [--db-path PATH] [--checkpoint PATH]
    python -m backend.scripts.verify_ledger --file <exported_calc.json>
    python -m backend.scripts.verify_ledger --create-checkpoint <out_checkpoint.json>
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.connection import DATABASE_URL, get_db_context, init_db
from backend.services.ledger_service import CalculationLedgerService


def verify_file(filepath: str) -> int:
    path = Path(filepath)
    if not path.exists():
        print(f"[-] Error: File not found at '{filepath}'")
        return 1

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        print(f"[-] Error reading/parsing JSON file: {exc}")
        return 1

    valid, err = CalculationLedgerService.verify_exported_record(data)
    calc_id = data.get("calculation_id", "UNKNOWN")
    seq = data.get("sequence_number", "UNKNOWN")
    current_hash = data.get("current_record_hash", "UNKNOWN")

    print(f"=== Sahi Daam Exported Record Verification ===")
    print(f"Calculation ID: {calc_id}")
    print(f"Sequence #:     {seq}")
    print(f"Record Hash:    {current_hash}")

    if valid:
        print("[+] VERIFICATION PASSED: Canonical SHA-256 digest matches the stored hash perfectly.")
        return 0
    else:
        print(f"[-] VERIFICATION FAILED: {err}")
        return 1


def create_checkpoint(output_path: str, db_url: str = None) -> int:
    try:
        init_db()
        with get_db_context() as session:
            ckpt = CalculationLedgerService.create_checkpoint(session)
            data = ckpt.model_dump()
            data["created_at"] = data["created_at"].isoformat()

            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            print(f"[+] Trusted checkpoint created at: {output_path}")
            print(f"    Checkpoint ID: {ckpt.checkpoint_id}")
            print(f"    Last Sequence: #{ckpt.last_verified_sequence}")
            print(f"    Last Hash:     {ckpt.last_record_hash}")
            return 0
    except Exception as exc:
        print(f"[-] Error creating checkpoint: {exc}")
        return 1


def verify_database_ledger(checkpoint_path: str = None) -> int:
    init_db()
    trusted_checkpoint = None
    if checkpoint_path:
        ckpt_p = Path(checkpoint_path)
        if not ckpt_p.exists():
            print(f"[-] Checkpoint file not found: {checkpoint_path}")
            return 1
        with open(ckpt_p, "r", encoding="utf-8") as f:
            trusted_checkpoint = json.load(f)

    with get_db_context() as session:
        res = CalculationLedgerService.verify_ledger(session, trusted_checkpoint=trusted_checkpoint)

    print("=== Sahi Daam Global Hash Chain Ledger Verification ===")
    print(f"Total Records:         {res.total_records}")
    print(f"Latest Sequence:       #{res.last_sequence_number if res.last_sequence_number is not None else 'None'}")
    print(f"Latest Tip Hash:       {res.last_record_hash if res.last_record_hash is not None else 'None'}")
    if trusted_checkpoint:
        print(f"Checkpoint Verified:   {res.checkpoint_verified}")

    if res.is_valid:
        print("[+] LEDGER INTEGRITY CONFIRMED: Chain is unbroken, sequences are contiguous, and all canonical hashes match.")
        return 0
    else:
        print(f"[-] LEDGER INTEGRITY VIOLATION DETECTED: {len(res.errors)} error(s) found.")
        for err in res.errors:
            print(f"    - {err}")
        if res.tampered_sequences:
            print(f"    Tampered sequences: {res.tampered_sequences}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Sahi Daam Ledger Verification & Checkpoint CLI")
    parser.add_argument("--file", type=str, help="Path to exported calculation JSON file to verify")
    parser.add_argument("--checkpoint", type=str, help="Path to trusted checkpoint JSON to verify against")
    parser.add_argument("--create-checkpoint", type=str, help="Path to save newly created trusted checkpoint JSON")

    args = parser.parse_args()

    if args.file:
        sys.exit(verify_file(args.file))
    elif args.create_checkpoint:
        sys.exit(create_checkpoint(args.create_checkpoint))
    else:
        sys.exit(verify_database_ledger(args.checkpoint))


if __name__ == "__main__":
    main()

"""Blockchain storage helpers and JSON utilities."""

import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, List

# Resolve data dir relative to this file so the app works from any CWD
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)

class Blockchain:
    def __init__(self):
        self.file_path = DATA_DIR / "blockchain.json"
        # Load an existing chain or bootstrap a fresh one
        self.chain = self.load_chain()
        if not self.chain:
            self.chain = [self.create_genesis_block()]
            self.save_chain()

    def create_genesis_block(self):
        ts = str(datetime.now())
        return {
            "index": 0,
            "timestamp": ts,
            "vote_data": "Genesis Block",
            "previous_hash": "0",
            "hash": self.calculate_hash(0, "0", ts, "Genesis Block"),
        }

    def calculate_hash(self, index, prev_hash, timestamp, data):
        value = f"{index}{prev_hash}{timestamp}{json.dumps(data)}"
        return hashlib.sha256(value.encode()).hexdigest()

    def add_block(self, vote_data):
        prev_block = self.chain[-1]
        new_index = prev_block["index"] + 1
        new_timestamp = str(datetime.now())
        new_hash = self.calculate_hash(new_index, prev_block["hash"], new_timestamp, vote_data)
        
        new_block = {
            "index": new_index,
            "timestamp": new_timestamp,
            "vote_data": vote_data,
            "previous_hash": prev_block["hash"],
            "hash": new_hash
        }
        self.chain.append(new_block)
        self.save_chain()
        return new_block

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            # Check current hash
            recalculated = self.calculate_hash(current["index"], current["previous_hash"], current["timestamp"], current["vote_data"])
            if current["hash"] != recalculated:
                return False, i
            
            # Check link
            if current["previous_hash"] != previous["hash"]:
                return False, i
        return True, -1

    def load_chain(self):
        return read_json("blockchain.json", default=[])

    def save_chain(self):
        write_json("blockchain.json", self.chain)

# Utility Functions
def hash_sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def read_json(filename: str, default: Any = None):
    """Read JSON safely; if missing/invalid return default and persist it."""
    path = DATA_DIR / filename
    if not path.exists():
        if default is not None:
            write_json(filename, default)
            # return a copy to avoid accidental mutation of the provided default
            return json.loads(json.dumps(default))
        return [] if default is None else default
    try:
        with path.open("r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        if default is not None:
            write_json(filename, default)
            return json.loads(json.dumps(default))
        return [] if default is None else default


def write_json(filename: str, data: Any):
    path = DATA_DIR / filename
    with path.open("w") as f:
        json.dump(data, f, indent=4)

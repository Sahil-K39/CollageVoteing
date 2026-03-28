from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from .models import VoterRegister, ElectionSet, Candidate, LoginData, VoteRequest
from .blockchain_logic import Blockchain, hash_sha256, read_json, write_json
import uuid
from datetime import datetime
import bcrypt
from pathlib import Path
import re

app = FastAPI(title="Blockchain Voting API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_ID = "admin123"
ADMIN_PASS = "admin_secure_password"  # In production, store hash/env

DEFAULT_CANDIDATES = [
    {"id": 1, "name": "Alice", "party": "Progressive"},
    {"id": 2, "name": "Bob", "party": "Unity"},
    {"id": 3, "name": "Chandra", "party": "Reform"},
]

def bootstrap_data():
    """Ensure data files contain valid JSON and seed defaults."""
    # Seed candidates if file is missing/empty/invalid
    candidates = read_json("candidates.json", default=DEFAULT_CANDIDATES)
    if not candidates:
        write_json("candidates.json", DEFAULT_CANDIDATES)

    # Do NOT auto-start an election; require admin to set window
    election = read_json("election.json", default={})
    if not election:
        write_json("election.json", {})

    # Seed empty voters list
    voters = read_json("voters.json", default=[])
    if voters is None:
        write_json("voters.json", [])

    # Chain is bootstrapped inside Blockchain


bootstrap_data()
bc = Blockchain()

# Serve the lightweight static UI (built in static_frontend)
STATIC_DIR = Path(__file__).resolve().parent.parent / "static_frontend"
if STATIC_DIR.exists():
    app.mount("/ui", StaticFiles(directory=STATIC_DIR, html=True), name="static-ui")
    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/ui")


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.2", "deployed_at": "2026-03-28"}

# --- AUTH & REGISTRATION ---

@app.post("/api/register")
def register_voter(voter: VoterRegister):
    voters = read_json("voters.json", default=[])
    
    # Validations
    if voter.age < 18: raise HTTPException(400, "Age must be 18+")
    validate_aadhaar(voter.aadhaar)
    validate_password(voter.password)
    
    hashed_aadhaar = hash_sha256(voter.aadhaar)
    if any(v["aadhaar"] == hashed_aadhaar for v in voters):
        raise HTTPException(400, "Aadhaar already registered")

    existing_ids = {v["voter_id"] for v in voters}
    voter_id = unique_voter_id(existing_ids)
    hashed_pass = bcrypt.hashpw(voter.password.encode(), bcrypt.gensalt()).decode()

    new_voter = {
        "voter_id": voter_id,
        "name": voter.name,
        "aadhaar": hashed_aadhaar,
        "gender": voter.gender,
        "constituency": voter.constituency,
        "password": hashed_pass,
        "has_voted": False
    }
    voters.append(new_voter)
    write_json("voters.json", voters)
    return {"message": "Registered", "voter_id": voter_id, "name": voter.name}


@app.post("/api/login")
def login_voter(data: LoginData):
    voters = read_json("voters.json", default=[])
    voter = next((v for v in voters if v["voter_id"] == data.id), None)
    if not voter:
        raise HTTPException(404, "Voter ID not found")

    if not bcrypt.checkpw(data.password.encode(), voter["password"].encode()):
        raise HTTPException(401, "Invalid credentials")

    return {
        "message": "Login successful",
        "voter_id": voter["voter_id"],
        "name": voter["name"],
        "has_voted": voter.get("has_voted", False),
    }


@app.post("/api/admin/login")
def admin_login(data: LoginData):
    if data.id != ADMIN_ID or data.password != ADMIN_PASS:
        raise HTTPException(401, "Invalid admin credentials")
    return {"message": "Admin authenticated"}

# --- ELECTION MANAGEMENT ---

@app.post("/api/admin/election")
def set_election(data: ElectionSet):
    if data.start_time >= data.end_time:
        raise HTTPException(400, "start_time must be before end_time")
    write_json("election.json", data.dict())
    return {"status": "Election Configured"}

@app.get("/api/election/status")
def get_status():
    config = read_json("election.json", default={})
    if not config or "start_time" not in config or "end_time" not in config:
        return "NOT_CONFIGURED"

    now = datetime.now().timestamp()
    if now < config["start_time"]:
        return "NOT_STARTED"
    if now > config["end_time"]:
        return "ENDED"
    return "ACTIVE"


@app.get("/api/election/config")
def get_election_config():
    return read_json("election.json", default={})

# --- Helpers ---

def validate_aadhaar(aadhaar: str):
    if not aadhaar.isdigit():
        raise HTTPException(400, "Aadhaar must be digits only")
    if len(aadhaar) != 12:
        raise HTTPException(400, "Aadhaar must be 12 digits")


def validate_password(pw: str):
    if len(pw) < 6 or len(pw) > 8:
        raise HTTPException(400, "Password must be 6-8 characters")
    if not re.search(r"[A-Z]", pw):
        raise HTTPException(400, "Password needs an uppercase letter")
    if not re.search(r"[a-z]", pw):
        raise HTTPException(400, "Password needs a lowercase letter")
    if not re.search(r"[0-9]", pw):
        raise HTTPException(400, "Password needs a number")
    if not re.search(r"[!@#$%^&*()_+\\-=[\\]{};':\",.<>/?]", pw):
        raise HTTPException(400, "Password needs a special character")


def unique_voter_id(existing_ids):
    while True:
        vid = str(uuid.uuid4())[:8]
        if vid not in existing_ids:
            return vid

# --- CANDIDATES & VOTING API ---

@app.get("/api/candidates")
def list_candidates():
    return read_json("candidates.json", default=DEFAULT_CANDIDATES)


@app.post("/api/admin/candidate")
def add_candidate(candidate: Candidate):
    candidates = read_json("candidates.json", default=DEFAULT_CANDIDATES)
    if any(c["id"] == candidate.id for c in candidates):
        raise HTTPException(400, "Candidate ID already exists")
    candidates.append(candidate.dict())
    write_json("candidates.json", candidates)
    return {"status": "added"}


@app.delete("/api/admin/candidate/{candidate_id}")
def remove_candidate(candidate_id: int):
    candidates = read_json("candidates.json", default=DEFAULT_CANDIDATES)
    new_list = [c for c in candidates if c["id"] != candidate_id]
    if len(new_list) == len(candidates):
        raise HTTPException(404, "Candidate not found")
    write_json("candidates.json", new_list)
    return {"status": "removed", "id": candidate_id}


@app.post("/api/vote")
def cast_vote(vote: VoteRequest):
    status = get_status()
    if status != "ACTIVE":
        raise HTTPException(400, f"Election is {status}")

    voters = read_json("voters.json", default=[])
    voter = next((v for v in voters if v["voter_id"] == vote.voter_id), None)

    if not voter:
        raise HTTPException(404, "Voter not found")
    if voter.get("has_voted"):
        raise HTTPException(400, "Already voted")

    candidates = read_json("candidates.json", default=DEFAULT_CANDIDATES)
    if not any(c["id"] == vote.candidate_id for c in candidates):
        raise HTTPException(404, "Candidate not found")

    # Add to Blockchain
    vote_payload = {
        "election_id": "ELC001",
        "voter_id": vote.voter_id,
        "candidate_id": vote.candidate_id,
        "timestamp": str(datetime.now()),
    }
    bc.add_block(vote_payload)

    # Update Voter Status
    for v in voters:
        if v["voter_id"] == vote.voter_id:
            v["has_voted"] = True
    write_json("voters.json", voters)

    return {"message": "Vote cast successfully"}

# --- RESULTS & TAMPERING ---

@app.get("/api/results")
def get_results(mode: str = "stop"):
    """mode: stop (block results if tampered) or warn (show partial with warning)."""
    if mode not in {"stop", "warn"}:
        raise HTTPException(400, "mode must be 'stop' or 'warn'")
    return compute_results(mode=mode)


def compute_results(mode: str = "stop"):
    """Verify chain, then return results depending on tamper mode."""
    is_valid, error_idx = bc.is_chain_valid()
    chain = bc.chain[1:]  # Skip genesis
    results = {}

    if not is_valid:
        tamper_block = bc.chain[error_idx]
        details = {
            "tampered_at": error_idx,
            "stored_hash": tamper_block["hash"],
            "recalculated_hash": bc.calculate_hash(
                tamper_block["index"],
                tamper_block["previous_hash"],
                tamper_block["timestamp"],
                tamper_block["vote_data"],
            ),
            "vote_data": tamper_block["vote_data"],
        }
        if mode == "stop":
            return {
                "results": {},
                "tamper_status": f"TAMPERING DETECTED at block {error_idx}. Results blocked.",
                "tamper_details": details,
            }
        # warn mode: show partial up to tamper
        valid_chain = bc.chain[1:error_idx]
        warning = f"TAMPERING DETECTED at block {error_idx}. Showing counts up to last valid block."
        for block in valid_chain:
            cid = str(block["vote_data"]["candidate_id"])
            results[cid] = results.get(cid, 0) + 1
        return {"results": results, "tamper_status": warning, "tamper_details": details}

    # valid chain
    for block in chain:
        cid = str(block["vote_data"]["candidate_id"])
        results[cid] = results.get(cid, 0) + 1
    return {"results": results, "tamper_status": "None"}

@app.post("/api/admin/tamper")
def simulate_tampering(block_index: int, fake_candidate_id: int):
    if block_index >= len(bc.chain): raise HTTPException(404, "Block not found")
    original = dict(bc.chain[block_index]["vote_data"])
    bc.chain[block_index]["vote_data"]["candidate_id"] = fake_candidate_id
    bc.save_chain()
    return {"message": f"Block {block_index} tampered successfully", "original_vote": original, "modified_vote": bc.chain[block_index]["vote_data"]}


@app.get("/api/admin/blocks")
def get_blocks():
    return {"chain": bc.chain}


@app.get("/api/admin/verify")
def verify_chain():
    valid, idx = bc.is_chain_valid()
    details = None
    if not valid:
        blk = bc.chain[idx]
        details = {
            "tampered_at": idx,
            "stored_hash": blk["hash"],
            "recalculated_hash": bc.calculate_hash(
                blk["index"], blk["previous_hash"], blk["timestamp"], blk["vote_data"]
            ),
            "vote_data": blk["vote_data"],
        }
    return {"is_valid": valid, "error_index": idx, "details": details}


@app.get("/api/admin/voters")
def list_voters():
    voters = read_json("voters.json", default=[])
    return [
        {
            "voter_id": v["voter_id"],
            "name": v.get("name"),
            "gender": v.get("gender"),
            "constituency": v.get("constituency"),
            "has_voted": v.get("has_voted", False),
        }
        for v in voters
    ]

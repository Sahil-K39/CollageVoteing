from pydantic import BaseModel
from typing import List, Literal

class VoterRegister(BaseModel):
    name: str
    age: int
    aadhaar: str
    gender: Literal["M","F","O","Male","Female","Other"]
    constituency: str
    password: str

class ElectionSet(BaseModel):
    election_id: str
    start_time: float # Use timestamps
    end_time: float

class Candidate(BaseModel):
    id: int
    name: str
    party: str

class LoginData(BaseModel):
    id: str
    password: str


class VoteRequest(BaseModel):
    voter_id: str
    candidate_id: int

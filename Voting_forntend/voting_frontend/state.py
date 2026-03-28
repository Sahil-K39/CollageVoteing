import datetime as dt
import httpx
import reflex as rx

API_BASE = "http://127.0.0.1:8000"


class State(rx.State):
    """Shared app state and API helpers."""

    # Voter session
    voter_id: str = ""
    voter_name: str = ""
    voter_password: str = ""
    voter_has_voted: bool = False
    is_logged_in: bool = False
    election_status: str = "UNKNOWN"
    message: str = ""
    tamper_status: str = ""

    # Collections
    candidates: list[dict] = []
    results: dict = {}

    # Registration form
    reg_name: str = ""
    reg_aadhaar: str = ""
    reg_dob: str = ""
    reg_password: str = ""

    # Login form
    voter_id_input: str = ""
    voter_password_input: str = ""

    # Admin
    admin_id: str = ""
    admin_password: str = ""
    admin_authed: bool = False
    form_start: str = ""
    form_end: str = ""
    new_candidate_name: str = ""
    new_candidate_party: str = ""
    new_candidate_id: str = ""

    @rx.var
    def age(self) -> int:
        if not self.reg_dob:
            return 0
        try:
            dob = dt.date.fromisoformat(self.reg_dob)
            today = dt.date.today()
            return int((today - dob).days // 365.25)
        except ValueError:
            return 0

    async def handle_registration(self):
        if self.age < 18:
            return rx.window_alert("You must be 18+ to register.")

        payload = {
            "name": self.reg_name,
            "age": self.age,
            "aadhaar": self.reg_aadhaar,
            "password": self.reg_password,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{API_BASE}/api/register", json=payload)
            except Exception as exc:  # network or connection failure
                return rx.window_alert(f"Registration failed: {exc}")

        if response.status_code == 200:
            data = response.json()
            self.voter_id = data["voter_id"]
            self.voter_name = data.get("name", "")
            self.message = "Registration successful. Save your Voter ID!"
            return rx.redirect("/vote")
        return rx.window_alert("Registration failed: " + response.text)

    async def fetch_status(self):
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{API_BASE}/api/election/status")
                self.election_status = resp.json()
            except Exception:
                self.election_status = "UNKNOWN"

    async def fetch_candidates(self):
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{API_BASE}/api/candidates")
                if resp.status_code == 200:
                    self.candidates = resp.json()
            except Exception:
                self.candidates = []

    async def fetch_results(self):
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{API_BASE}/api/results")
                if resp.status_code == 200:
                    data = resp.json()
                    self.results = data.get("results", {})
                    self.tamper_status = data.get("tamper_status", "")
            except Exception:
                self.results = {}

    async def login_voter(self):
        payload = {"id": self.voter_id_input, "password": self.voter_password_input}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{API_BASE}/api/login", json=payload)
            except Exception as exc:
                return rx.window_alert(f"Login failed: {exc}")

        if resp.status_code != 200:
            return rx.window_alert("Login failed: " + resp.text)

        data = resp.json()
        self.voter_id = data["voter_id"]
        self.voter_name = data.get("name", "")
        self.voter_has_voted = data.get("has_voted", False)
        self.is_logged_in = True
        self.message = "Logged in"
        await self.fetch_candidates()
        await self.fetch_results()

    async def cast_vote(self, candidate_id: int):
        if not self.is_logged_in:
            return rx.window_alert("Login first")
        if self.voter_has_voted:
            return rx.window_alert("You have already voted")

        payload = {"voter_id": self.voter_id, "candidate_id": candidate_id}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{API_BASE}/api/vote", json=payload)
            except Exception as exc:
                return rx.window_alert(f"Vote failed: {exc}")

        if resp.status_code == 200:
            self.voter_has_voted = True
            self.message = "Vote recorded on blockchain"
            await self.fetch_results()
        else:
            return rx.window_alert("Vote failed: " + resp.text)

    async def refresh_all(self):
        await self.fetch_status()
        await self.fetch_candidates()
        await self.fetch_results()

    # Admin helpers
    async def admin_login(self):
        payload = {"id": self.admin_id, "password": self.admin_password}
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{API_BASE}/api/admin/login", json=payload)
        if resp.status_code == 200:
            self.admin_authed = True
            self.message = "Admin authenticated"
        else:
            return rx.window_alert("Admin login failed: " + resp.text)

    async def admin_set_election(self):
        if not self.admin_authed:
            return rx.window_alert("Admin login required")
        try:
            start_ts = dt.datetime.fromisoformat(self.form_start).timestamp()
            end_ts = dt.datetime.fromisoformat(self.form_end).timestamp()
        except Exception:
            return rx.window_alert("Invalid date/time format")
        payload = {"election_id": "ELC001", "start_time": start_ts, "end_time": end_ts}
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{API_BASE}/api/admin/election", json=payload)
        if resp.status_code == 200:
            await self.fetch_status()
            self.message = "Election window updated"
        else:
            return rx.window_alert("Failed: " + resp.text)

    async def admin_add_candidate(self):
        if not self.admin_authed:
            return rx.window_alert("Admin login required")
        try:
            cid = int(self.new_candidate_id)
        except ValueError:
            return rx.window_alert("Candidate ID must be a number")
        payload = {"id": cid, "name": self.new_candidate_name, "party": self.new_candidate_party}
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{API_BASE}/api/admin/candidate", json=payload)
        if resp.status_code == 200:
            await self.fetch_candidates()
            self.message = "Candidate added"
        else:
            return rx.window_alert("Add candidate failed: " + resp.text)

import reflex as rx
from ..state import State


def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Secure Blockchain Voting", size="9", color_scheme="blue"),
            rx.text(
                "A transparent, tamper-proof election system powered by FastAPI + Reflex",
                size="5",
            ),
            rx.hstack(
                rx.link(
                    rx.button("Voter Portal", size="4", color_scheme="blue"),
                    href="/vote",
                ),
                rx.link(
                    rx.button("Register", size="4", variant="outline"),
                    href="/register",
                ),
                rx.link(
                    rx.button("Admin", size="4", variant="ghost"),
                    href="/admin",
                ),
                spacing="4",
                margin_top="2em",
            ),
            rx.text("Election status: ", rx.badge(State.election_status), size="4"),
            align="center",
            spacing="5",
            on_mount=State.fetch_status,
        ),
        height="100vh",
        background="radial-gradient(circle at top, #1e293b, #0f172a)",
    )

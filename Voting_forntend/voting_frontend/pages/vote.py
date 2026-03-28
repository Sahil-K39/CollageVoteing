import reflex as rx
from ..state import State


def vote() -> rx.Component:
    return rx.vstack(
        rx.heading("Voter Portal", size="7"),
        rx.text("Cast your ballot securely. Blockchain-backed and tamper-evident."),

        rx.box(
            rx.cond(
                State.is_logged_in,
                rx.vstack(
                    rx.text(f"Logged in as {State.voter_name or 'Voter'} ({State.voter_id})"),
                    rx.badge("Already voted" if State.voter_has_voted else "Ready to vote", color_scheme="green" if State.voter_has_voted else "blue"),
                    align="start",
                    spacing="2",
                ),
                rx.vstack(
                    rx.input(placeholder="Voter ID", on_change=State.set_voter_id_input, width="100%"),
                    rx.input(type="password", placeholder="Password", on_change=State.set_voter_password_input, width="100%"),
                    rx.button("Login", on_click=State.login_voter, width="100%", color_scheme="blue"),
                    align="start",
                    spacing="3",
                ),
            ),
            padding="1.5em",
            border="1px solid #e2e8f0",
            border_radius="12px",
            width="100%",
        ),

        rx.hstack(
            rx.text("Election status:"),
            rx.badge(State.election_status, color_scheme="orange"),
            rx.button("Refresh", size="2", variant="soft", on_click=State.refresh_all),
            spacing="3",
        ),

        rx.vstack(
            rx.heading("Candidates", size="6"),
            rx.text("Select one candidate and submit your vote."),
            rx.grid(
                *[
                    rx.card(
                        rx.vstack(
                            rx.heading(c.get("name", ""), size="5"),
                            rx.text(c.get("party", ""), color="gray"),
                            rx.text(f"ID: {c.get('id')}"),
                            rx.button(
                                "Cast Vote",
                                on_click=lambda cid=c.get("id"): State.cast_vote(cid),
                                disabled=State.voter_has_voted,
                                color_scheme="blue",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        padding="1.5em",
                    )
                    for c in State.candidates
                ],
                columns="repeat(auto-fit, minmax(220px, 1fr))",
                spacing="4",
                width="100%",
            ),
            width="100%",
        ),

        rx.vstack(
            rx.hstack(
                rx.heading("Live Results", size="6"),
                rx.button("Refresh", size="2", on_click=State.fetch_results),
                spacing="3",
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Candidate ID"),
                        rx.table.column_header_cell("Votes"),
                    )
                ),
                rx.table.body(
                    *[
                        rx.table.row(
                            rx.table.cell(str(cid)),
                            rx.table.cell(str(count)),
                        )
                        for cid, count in State.results.items()
                    ]
                ),
                width="100%",
            ),
            rx.cond(
                State.tamper_status,
                rx.badge(State.tamper_status, color_scheme="red"),
                rx.box(),
            ),
            width="100%",
        ),

        rx.cond(State.message != "", rx.callout(State.message, icon="info"), rx.box()),
        spacing="6",
        padding="2em",
        max_width="1000px",
        width="100%",
        on_mount=State.refresh_all,
    )

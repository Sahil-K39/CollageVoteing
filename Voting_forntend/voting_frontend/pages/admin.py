import reflex as rx
from ..state import State


def admin() -> rx.Component:
    return rx.vstack(
        rx.heading("Admin Control Panel", size="7"),
        rx.text("Configure election window and manage candidates."),

        rx.box(
            rx.cond(
                State.admin_authed,
                rx.callout("Authenticated as admin", icon="shield"),
                rx.vstack(
                    rx.input(placeholder="Admin ID", on_change=State.set_admin_id, width="100%"),
                    rx.input(type="password", placeholder="Password", on_change=State.set_admin_password, width="100%"),
                    rx.button("Login", on_click=State.admin_login, width="100%", color_scheme="blue"),
                    spacing="3",
                    align="start",
                ),
            ),
            padding="1.5em",
            border="1px solid #e2e8f0",
            border_radius="12px",
            width="100%",
        ),

        rx.cond(
            State.admin_authed,
            rx.vstack(
                rx.hstack(
                    rx.heading("Election Window", size="5"),
                    rx.badge(State.election_status),
                    spacing="3",
                ),
                rx.hstack(
                    rx.input(type="datetime-local", placeholder="Start", on_change=State.set_form_start),
                    rx.input(type="datetime-local", placeholder="End", on_change=State.set_form_end),
                    rx.button("Update", on_click=State.admin_set_election, color_scheme="blue"),
                    spacing="3",
                ),
                rx.divider(),
                rx.heading("Add Candidate", size="5"),
                rx.grid(
                    rx.input(placeholder="ID", on_change=State.set_new_candidate_id),
                    rx.input(placeholder="Name", on_change=State.set_new_candidate_name),
                    rx.input(placeholder="Party", on_change=State.set_new_candidate_party),
                    columns="3",
                    spacing="3",
                    width="100%",
                ),
                rx.button("Add", on_click=State.admin_add_candidate, color_scheme="green", width="150px"),
                rx.divider(),
                rx.heading("Live Results", size="5"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Candidate ID"),
                            rx.table.column_header_cell("Votes"),
                        )
                    ),
                    rx.table.body(
                        *[
                            rx.table.row(rx.table.cell(str(cid)), rx.table.cell(str(count)))
                            for cid, count in State.results.items()
                        ]
                    ),
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            rx.box(),
        ),

        rx.cond(State.message != "", rx.callout(State.message, icon="info"), rx.box()),
        spacing="6",
        padding="2em",
        max_width="1000px",
        width="100%",
        on_mount=State.refresh_all,
    )

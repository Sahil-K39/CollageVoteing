import reflex as rx
from ..state import State

def register() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Voter Registration", size="6"),
                rx.text("Enter your details to generate a unique Voter ID"),
                rx.input(placeholder="Full Name", on_blur=State.set_reg_name, width="100%"),
                rx.input(type="date", on_change=State.set_reg_dob, width="100%"),
                rx.input(placeholder="Aadhaar Number (12 Digits)", on_blur=State.set_reg_aadhaar, width="100%"),
                rx.input(type="password", placeholder="Password", on_blur=State.set_reg_password, width="100%"),
                
                rx.cond(
                    State.age < 18,
                    rx.text("Must be 18 or older", color="red"),
                    rx.button("Register", on_click=State.handle_registration, width="100%", color_scheme="blue")
                ),
                spacing="4",
                width="400px",
            ),
            padding="2em",
        ),
        padding_top="5em",
    )
"""Blinded A/B behavioural experiment for discount framing."""

from __future__ import annotations

import csv
import secrets
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent

# These image files must be uploaded to the main GitHub folder.
ADS = {
    "A": BASE_DIR / "Version 1.png",  # 20% OFF
    "B": BASE_DIR / "Version 2.png",  # SAVE ₹500 TODAY
}

RESPONSES_FILE = BASE_DIR / "data" / "behavioural_responses.csv"

FIELDNAMES = [
    "respondent_id",
    "participant_id",
    "timestamp_utc",
    "assigned_group",
    "decision",
    "decision_time_seconds",
]


def initialise_session():
    defaults = {
        "page": "welcome",
        "respondent_id": None,
        "assigned_group": None,
        "participant_id": "",
        "ad_exposure_started_at": None,
        "decision": None,
        "decision_time_seconds": None,
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def begin_experiment(participant_id):
    """Assign one ad randomly for this participant session."""

    st.session_state.respondent_id = f"R-{uuid.uuid4().hex[:8].upper()}"
    st.session_state.assigned_group = secrets.choice(("A", "B"))
    st.session_state.participant_id = participant_id.strip()
    st.session_state.ad_exposure_started_at = None
    st.session_state.decision = None
    st.session_state.decision_time_seconds = None
    st.session_state.page = "offer"


def save_response(record):
    """Append the response without overwriting earlier responses."""

    RESPONSES_FILE.parent.mkdir(exist_ok=True)
    file_exists = RESPONSES_FILE.exists()

    with RESPONSES_FILE.open("a", newline="", encoding="utf-8") as response_file:
        writer = csv.DictWriter(response_file, fieldnames=FIELDNAMES)

        if not file_exists:
            writer.writeheader()

        writer.writerow(record)


def render_welcome():
    st.markdown(
        "<div class='brand'>SOUNDX <span>SHOPPING LAB</span></div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='hero-kicker'>A short consumer activity</div>",
        unsafe_allow_html=True,
    )

    st.title("Discover your next sound experience")

    st.write(
        "Imagine you are browsing online and find a product offer. "
        "View it as you normally would when shopping online."
    )

    st.markdown(
        """
        <div class='feature-row'>
            <div><b>01</b><br><span>View an offer</span></div>
            <div><b>02</b><br><span>Make a choice</span></div>
            <div><b>03</b><br><span>You're done</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("welcome_form", border=False):
        participant_id = st.text_input(
            "Participant ID (optional)",
            placeholder="For example, P001",
            help="Leave blank if you do not have an ID.",
        )

        st.caption("Estimated time: less than one minute.")

        start = st.form_submit_button(
            "Start shopping activity  →",
            type="primary",
            use_container_width=True,
        )

    if start:
        begin_experiment(participant_id)
        st.rerun()


def render_offer():
    # Prevent a second decision in the same session.
    if st.session_state.decision is not None:
        st.session_state.page = "thank_you"
        st.rerun()

    ad_path = ADS[st.session_state.assigned_group]

    if not ad_path.exists():
        st.error(
            "The assigned product image is unavailable. "
            "Please check that Version 1.png and Version 2.png "
            "are uploaded to your GitHub repository."
        )
        st.stop()

    # Invisible timer starts once, when the participant sees the assigned ad.
    if st.session_state.ad_exposure_started_at is None:
        st.session_state.ad_exposure_started_at = time.perf_counter()

    st.progress(0.5, text="Step 1 of 2")

    st.markdown(
        "<div class='hero-kicker'>Your selected offer</div>",
        unsafe_allow_html=True,
    )

    st.title("A closer look")

    st.write(
        "Imagine this product appeared while you were shopping online. "
        "What would you like to do?"
    )

    st.image(str(ad_path), use_container_width=True)

    st.markdown(
        "<div class='quiet-note'>Choose the option that best reflects your natural shopping decision.</div>",
        unsafe_allow_html=True,
    )

    add_to_cart_column, not_interested_column = st.columns(2)

    with add_to_cart_column:
        chose_add_to_cart = st.button(
            "🛒  ADD TO CART",
            type="primary",
            use_container_width=True,
        )

    with not_interested_column:
        chose_not_interested = st.button(
            "NOT INTERESTED",
            use_container_width=True,
        )

    if chose_add_to_cart or chose_not_interested:
        decision = (
            "ADD_TO_CART"
            if chose_add_to_cart
            else "NOT_INTERESTED"
        )

        decision_time = round(
            time.perf_counter()
            - st.session_state.ad_exposure_started_at,
            3,
        )

        st.session_state.decision = decision
        st.session_state.decision_time_seconds = decision_time

        save_response(
            {
                "respondent_id": st.session_state.respondent_id,
                "participant_id": st.session_state.participant_id,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "assigned_group": st.session_state.assigned_group,
                "decision": decision,
                "decision_time_seconds": decision_time,
            }
        )

        st.session_state.page = "thank_you"
        st.rerun()


def render_thank_you():
    st.progress(1.0, text="Step 2 of 2")

    st.markdown(
        "<div class='thank-you-mark'>✓</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='hero-kicker'>Response received</div>",
        unsafe_allow_html=True,
    )

    st.title("Thank you")

    st.write(
        "Your response has been recorded. "
        "Your participation is now complete."
    )

    st.info("You may now close this page.")


def main():
    st.set_page_config(
        page_title="SoundX Shopping Activity",
        page_icon="🎧",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at 15% 0%, #e9f8ef 0, transparent 27%),
                #fbfcfa;
            color: #15251b;
        }

        .block-container {
            max-width: 790px;
            padding: 3.5rem 2rem 4rem;
        }

        .brand {
            color: #17251c;
            font-size: .9rem;
            font-weight: 850;
            letter-spacing: .1em;
            margin-bottom: 3.6rem;
        }

        .brand span {
            color: #2c9b60;
            font-weight: 650;
        }

        .hero-kicker {
            color: #16834b;
            font-size: .78rem;
            font-weight: 800;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin-bottom: .55rem;
        }

        h1 {
            color: #16261b;
            font-size: clamp(2.1rem, 5vw, 3.35rem) !important;
            line-height: 1.08;
            letter-spacing: -.045em;
            margin-bottom: .8rem;
        }

        .feature-row {
            display: flex;
            gap: 1px;
            background: #dfe8e1;
            border: 1px solid #dfe8e1;
            border-radius: 14px;
            overflow: hidden;
            margin: 2rem 0;
        }

        .feature-row div {
            flex: 1;
            background: rgba(255, 255, 255, .76);
            padding: 1rem;
        }

        .feature-row b {
            color: #16834b;
            font-size: 1.1rem;
        }

        .feature-row span {
            color: #5b675f;
            font-size: .83rem;
        }

        [data-testid='stForm'] {
            background: #ffffff;
            border: 1px solid #e2e9e4;
            box-shadow: 0 12px 30px rgba(23, 54, 34, .05);
            border-radius: 18px;
            padding: 1.4rem;
        }

        .quiet-note {
            color: #627067;
            font-size: .88rem;
            text-align: center;
            margin: 1.2rem 0;
        }

        .thank-you-mark {
            background: #18864d;
            color: white;
            width: 58px;
            height: 58px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            font-size: 1.8rem;
            margin-bottom: 1.4rem;
        }

        .stButton > button {
            background: #16834b;
            border: none;
            border-radius: 10px;
            font-weight: 750;
            min-height: 3rem;
        }

        .stButton > button:hover {
            background: #0e6738;
        }

        [data-testid='stProgressBar'] > div > div {
            background: #16834b;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    initialise_session()

    pages = {
        "welcome": render_welcome,
        "offer": render_offer,
        "thank_you": render_thank_you,
    }

    pages[st.session_state.page]()


if __name__ == "__main__":
    main()

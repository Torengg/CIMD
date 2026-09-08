"""Blinded A/B data-collection app for discount-framing research."""
from __future__ import annotations

import secrets
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent

ADS = {
    "A": BASE_DIR / "Version 1.png",
    "B": BASE_DIR / "Version 2.png",
}

try:
    GOOGLE_SHEETS_URL = st.secrets["google_sheets"]["web_app_url"]
    GOOGLE_SHEETS_KEY = st.secrets["google_sheets"]["api_key"]
except Exception:
    GOOGLE_SHEETS_URL = ""
    GOOGLE_SHEETS_KEY = ""


def initialise_session():
    defaults = {
        "page": "welcome",
        "respondent_id": None,
        "assigned_group": None,
        "participant_id": "",
        "ad_exposure_started_at": None,
        "decision": None,
        "decision_time_seconds": None,
        "decision_saved": False,
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def begin_experiment(participant_id):
    st.session_state.respondent_id = f"R-{uuid.uuid4().hex[:8].upper()}"
    st.session_state.assigned_group = secrets.choice(("A", "B"))
    st.session_state.participant_id = participant_id.strip()
    st.session_state.ad_exposure_started_at = None
    st.session_state.decision = None
    st.session_state.decision_time_seconds = None
    st.session_state.decision_saved = False
    st.session_state.page = "offer"


def save_response(record):
    if not GOOGLE_SHEETS_URL or not GOOGLE_SHEETS_KEY:
        return False, "The Google Sheet connection has not been configured yet."

    try:
        response = requests.post(
            GOOGLE_SHEETS_URL,
            json={**record, "api_key": GOOGLE_SHEETS_KEY},
            timeout=15,
        )
        response.raise_for_status()

        if response.json().get("ok") is not True:
            return False, "The response could not be saved. Please try again."

    except (requests.RequestException, ValueError) as error:
        return False, f"Could not save your response: {error}"

    return True, ""


def decision_record():
    return {
        "respondent_id": st.session_state.respondent_id,
        "participant_id": st.session_state.participant_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "assigned_group": st.session_state.assigned_group,
        "decision": st.session_state.decision,
        "decision_time_seconds": st.session_state.decision_time_seconds,
    }


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

    with st.form("welcome_form", border=False):
        participant_id = st.text_input(
            "Participant ID (optional)",
            placeholder="For example, P001",
        )

        start = st.form_submit_button(
            "Start shopping activity →",
            type="primary",
            use_container_width=True,
        )

    if start:
        begin_experiment(participant_id)
        st.rerun()


def render_offer():
    if st.session_state.decision_saved:
        st.session_state.page = "thank_you"
        st.rerun()

    ad_path = ADS[st.session_state.assigned_group]

    if not ad_path.exists():
        st.error(
            "The assigned product image is unavailable. "
            "Check that Version 1.png and Version 2.png "
            "are uploaded in GitHub."
        )
        st.stop()

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

    if st.session_state.decision is None:
        add_to_cart, not_interested = st.columns(2)

        with add_to_cart:
            chose_cart = st.button(
                "🛒 ADD TO CART",
                type="primary",
                use_container_width=True,
            )

        with not_interested:
            chose_not_interested = st.button(
                "NOT INTERESTED",
                use_container_width=True,
            )

        if chose_cart or chose_not_interested:
            st.session_state.decision = (
                "ADD_TO_CART"
                if chose_cart
                else "NOT_INTERESTED"
            )

            st.session_state.decision_time_seconds = round(
                time.perf_counter()
                - st.session_state.ad_exposure_started_at,
                3,
            )

            saved, message = save_response(decision_record())

            if saved:
                st.session_state.decision_saved = True
                st.session_state.page = "thank_you"
                st.rerun()

            st.error(message)

    else:
        st.warning("Your choice was captured but has not yet been saved.")

        if st.button(
            "Retry saving my response",
            type="primary",
            use_container_width=True,
        ):
            saved, message = save_response(decision_record())

            if saved:
                st.session_state.decision_saved = True
                st.session_state.page = "thank_you"
                st.rerun()

            st.error(message)


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
    st.write("Your response has been recorded.")
    st.info("You may now close this page.")


def main():
    st.set_page_config(
        page_title="SoundX Shopping Activity",
        page_icon="🎧",
        layout="centered",
    )

    st.markdown(
        """
        <style>
        .stApp {
            background: #fbfcfa;
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
        }

        .hero-kicker {
            color: #16834b;
            font-size: .78rem;
            font-weight: 800;
            letter-spacing: .12em;
            text-transform: uppercase;
        }

        h1 {
            color: #16261b;
        }

        .quiet-note {
            color: #627067;
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

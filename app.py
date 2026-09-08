"""Blinded A/B data-collection app for discount-framing research."""

from __future__ import annotations

import csv
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
ADS = {
    "A": BASE_DIR / "Version 1.png",
    "B": BASE_DIR / "Version 2.png",
}
RESPONSES_FILE = BASE_DIR / "data" / "responses.csv"

FIELDNAMES = [
    "respondent_id",
    "participant_id",
    "timestamp_utc",
    "assigned_group",
    "online_purchase_last_6_months",
    "shopping_frequency",
    "discount_importance",
    "purchase_likelihood",
    "purchase_consideration",
    "offer_choice_likelihood",
    "purchase_intention_index",
    "discount_communication_recall",
    "discount_clarity",
]


def initialise_session() -> None:
    defaults = {
        "page": "welcome",
        "respondent_id": None,
        "assigned_group": None,
        "participant_id": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def begin_experiment(participant_id: str) -> None:
    # This happens once per browser session. The other treatment is never rendered.
    st.session_state.respondent_id = f"R-{uuid.uuid4().hex[:8].upper()}"
    st.session_state.assigned_group = secrets.choice(("A", "B"))
    st.session_state.participant_id = participant_id.strip()
    st.session_state.page = "survey"


def save_response(record: dict) -> None:
    RESPONSES_FILE.parent.mkdir(exist_ok=True)
    file_exists = RESPONSES_FILE.exists()
    with RESPONSES_FILE.open("a", newline="", encoding="utf-8") as response_file:
        writer = csv.DictWriter(response_file, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)


def scale_question(label: str, key: str, help_text: str | None = None) -> int:
    return st.radio(
        label,
        options=range(1, 8),
        index=None,
        horizontal=True,
        key=key,
        help=help_text,
    )


def render_welcome() -> None:
    st.markdown("<div class='eyebrow'>Consumer shopping survey</div>", unsafe_allow_html=True)
    st.title("A short online-shopping activity")
    st.write(
        "Imagine you are browsing an online store. You will see one product offer and "
        "answer a few questions about it. There are no right or wrong answers."
    )
    st.info("Please complete the activity independently. It takes about two minutes.")
    with st.form("welcome_form"):
        participant_id = st.text_input(
            "Participant ID (optional)",
            placeholder="For example: P001",
            help="Leave blank if you do not have an ID; a respondent ID will be generated automatically.",
        )
        start = st.form_submit_button("Begin", type="primary", use_container_width=True)
    if start:
        begin_experiment(participant_id)
        st.rerun()


def render_survey() -> None:
    group = st.session_state.assigned_group
    ad_path = ADS[group]
    if not ad_path.exists():
        st.error("The assigned product image is unavailable. Please contact the researcher.")
        st.stop()

    st.markdown("<div class='eyebrow'>Please view the offer</div>", unsafe_allow_html=True)
    st.title("Wireless headphones")
    st.image(str(ad_path), use_container_width=True)
    st.caption("Please answer based on the offer you have just viewed.")

    with st.form("response_form"):
        st.subheader("Your view of this offer")
        st.caption("Use 1 = very unlikely / strongly disagree and 7 = very likely / strongly agree.")
        q1 = scale_question("How likely are you to purchase this product?", "q1")
        q2 = scale_question("How likely are you to consider purchasing this product?", "q2")
        q3 = scale_question("How likely are you to choose this offer over similar offers?", "q3")

        st.subheader("A few short background questions")
        bought_online = st.radio(
            "Have you made an online purchase in the last 6 months?",
            ["Yes", "No", "Prefer not to say"],
            index=None,
            horizontal=True,
        )
        shopping_frequency = st.selectbox(
            "How often do you shop online?",
            ["Select an answer", "Rarely", "Occasionally", "About monthly", "Weekly", "Several times a week"],
        )
        discount_importance = scale_question(
            "How important are discounts when you make an online purchase?", "discount_importance"
        )

        st.subheader("About the offer")
        recall = st.radio(
            "How was the discount communicated in the offer?",
            ["Percentage discount", "Rupee amount saved", "I do not remember"],
            index=None,
            horizontal=True,
        )
        clarity = scale_question("How clearly was the discount communicated?", "clarity")
        submitted = st.form_submit_button("Submit response", type="primary", use_container_width=True)

    if submitted:
        required = [q1, q2, q3, bought_online, discount_importance, recall, clarity]
        if any(value is None for value in required) or shopping_frequency == "Select an answer":
            st.error("Please answer every question before submitting.")
            return

        pii = round((q1 + q2 + q3) / 3, 2)
        save_response(
            {
                "respondent_id": st.session_state.respondent_id,
                "participant_id": st.session_state.participant_id,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "assigned_group": group,
                "online_purchase_last_6_months": bought_online,
                "shopping_frequency": shopping_frequency,
                "discount_importance": discount_importance,
                "purchase_likelihood": q1,
                "purchase_consideration": q2,
                "offer_choice_likelihood": q3,
                "purchase_intention_index": pii,
                "discount_communication_recall": recall,
                "discount_clarity": clarity,
            }
        )
        st.session_state.page = "thank_you"
        st.rerun()


def render_thank_you() -> None:
    st.success("Your response has been recorded.")
    st.title("Thank you")
    st.write("Your participation is complete. You may now close this page.")


def main() -> None:
    st.set_page_config(page_title="Consumer Shopping Survey", page_icon="🛍️", layout="centered")
    st.markdown(
        """
        <style>
        .stApp { background: #fafaf8; }
        .block-container { max-width: 820px; padding-top: 3.5rem; padding-bottom: 3rem; }
        .eyebrow { color: #167c4a; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; font-size: .78rem; }
        h1, h2, h3 { color: #18231d; }
        [data-testid='stForm'] { background: white; border: 1px solid #e5e8e3; border-radius: 14px; padding: 1.5rem; }
        .stButton > button { background: #167c4a; border: 0; font-weight: 650; }
        .stButton > button:hover { background: #0e6338; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    initialise_session()
    {"welcome": render_welcome, "survey": render_survey, "thank_you": render_thank_you}[st.session_state.page]()


if __name__ == "__main__":
    main()

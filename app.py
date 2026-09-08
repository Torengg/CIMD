"""Blinded A/B data-collection app for discount-framing research."""
from __future__ import annotations

import csv
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
# The deployed GitHub repository stores both images beside app.py.
ADS = {"A": BASE_DIR / "Version 1.png", "B": BASE_DIR / "Version 2.png"}
RESPONSES_FILE = BASE_DIR / "data" / "responses.csv"
FIELDNAMES = [
    "respondent_id", "participant_id", "timestamp_utc", "assigned_group",
    "online_purchase_last_6_months", "shopping_frequency", "discount_importance",
    "purchase_likelihood", "purchase_consideration", "offer_choice_likelihood",
    "purchase_intention_index", "discount_communication_recall", "discount_clarity",
]


def initialise_session() -> None:
    for key, value in {"page": "welcome", "respondent_id": None, "assigned_group": None, "participant_id": ""}.items():
        st.session_state.setdefault(key, value)


def begin_experiment(participant_id: str) -> None:
    """Assign exactly one treatment for the lifetime of this browser session."""
    st.session_state.respondent_id = f"R-{uuid.uuid4().hex[:8].upper()}"
    st.session_state.assigned_group = secrets.choice(("A", "B"))
    st.session_state.participant_id = participant_id.strip()
    st.session_state.page = "offer"


def save_response(record: dict) -> None:
    RESPONSES_FILE.parent.mkdir(exist_ok=True)
    has_header = RESPONSES_FILE.exists()
    with RESPONSES_FILE.open("a", newline="", encoding="utf-8") as response_file:
        writer = csv.DictWriter(response_file, fieldnames=FIELDNAMES)
        if not has_header:
            writer.writeheader()
        writer.writerow(record)


def progress(current: int) -> None:
    st.progress(current / 3, text=f"Step {current} of 3")


def rating(label: str, key: str, low: str, high: str) -> int:
    st.markdown(f"<div class='question-label'>{label}</div>", unsafe_allow_html=True)
    answer = st.radio(label, range(1, 8), index=None, horizontal=True, key=key, label_visibility="collapsed")
    st.markdown(f"<div class='scale-labels'><span>{low}</span><span>{high}</span></div>", unsafe_allow_html=True)
    return answer


def render_welcome() -> None:
    st.markdown("<div class='brand'>SOUNDX <span>SHOPPING LAB</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-kicker'>A short consumer activity</div>", unsafe_allow_html=True)
    st.title("Discover your next sound experience")
    st.write("Imagine you are browsing online and find a product offer. Take a moment to view it, then tell us what you think.")
    st.markdown("""<div class='feature-row'><div><b>01</b><br><span>View an offer</span></div><div><b>02</b><br><span>Share your view</span></div><div><b>03</b><br><span>You're done</span></div></div>""", unsafe_allow_html=True)
    with st.form("welcome_form", border=False):
        participant_id = st.text_input("Participant ID (optional)", placeholder="For example, P001", help="Leave blank if you do not have an ID. A study ID will be generated automatically.")
        st.caption("Estimated time: about 2 minutes · Please complete this independently.")
        if st.form_submit_button("Start shopping activity  →", type="primary", use_container_width=True):
            begin_experiment(participant_id)
            st.rerun()


def render_offer() -> None:
    ad_path = ADS[st.session_state.assigned_group]
    if not ad_path.exists():
        st.error("The assigned product image is unavailable. Please contact the researcher.")
        st.stop()
    progress(1)
    st.markdown("<div class='hero-kicker'>Your selected offer</div>", unsafe_allow_html=True)
    st.title("A closer look")
    st.write("Imagine this product appeared while you were shopping online. View the offer as you normally would.")
    st.image(str(ad_path), use_container_width=True)
    st.markdown("<div class='quiet-note'>Take a moment to look at the product details and offer.</div>", unsafe_allow_html=True)
    if st.button("I've viewed the offer  →", type="primary", use_container_width=True):
        st.session_state.page = "survey"
        st.rerun()


def render_survey() -> None:
    progress(2)
    st.markdown("<div class='hero-kicker'>Your reaction</div>", unsafe_allow_html=True)
    st.title("Tell us what you think")
    st.write("There are no right or wrong answers. Please respond based on the offer you just viewed.")
    with st.form("response_form", border=False):
        st.markdown("<div class='section-heading'>Your purchase intention</div>", unsafe_allow_html=True)
        st.caption("Choose a number from 1 to 7 for each statement.")
        q1 = rating("How likely are you to purchase this product?", "q1", "1 · Very unlikely", "7 · Very likely")
        q2 = rating("How likely are you to consider purchasing this product?", "q2", "1 · Very unlikely", "7 · Very likely")
        q3 = rating("How likely are you to choose this offer over similar offers?", "q3", "1 · Very unlikely", "7 · Very likely")
        st.markdown("<div class='section-heading'>A little about you</div>", unsafe_allow_html=True)
        bought_online = st.radio("Have you made an online purchase in the last 6 months?", ["Yes", "No", "Prefer not to say"], index=None, horizontal=True)
        shopping_frequency = st.select_slider("How often do you shop online?", options=["Rarely", "Occasionally", "About monthly", "Weekly", "Several times a week"], value=None)
        discount_importance = rating("How important are discounts when you make an online purchase?", "discount_importance", "1 · Not important", "7 · Extremely important")
        st.markdown("<div class='section-heading'>About the offer</div>", unsafe_allow_html=True)
        recall = st.radio("How was the discount communicated in the offer?", ["Percentage discount", "Rupee amount saved", "I do not remember"], index=None, horizontal=True)
        clarity = rating("How clearly was the discount communicated?", "clarity", "1 · Not at all clear", "7 · Extremely clear")
        submitted = st.form_submit_button("Submit my response  →", type="primary", use_container_width=True)
    if submitted:
        required = [q1, q2, q3, bought_online, shopping_frequency, discount_importance, recall, clarity]
        if any(value is None for value in required):
            st.error("Please answer every question before submitting.")
            return
        pii = round((q1 + q2 + q3) / 3, 2)
        save_response({"respondent_id": st.session_state.respondent_id, "participant_id": st.session_state.participant_id, "timestamp_utc": datetime.now(timezone.utc).isoformat(), "assigned_group": st.session_state.assigned_group, "online_purchase_last_6_months": bought_online, "shopping_frequency": shopping_frequency, "discount_importance": discount_importance, "purchase_likelihood": q1, "purchase_consideration": q2, "offer_choice_likelihood": q3, "purchase_intention_index": pii, "discount_communication_recall": recall, "discount_clarity": clarity})
        st.session_state.page = "thank_you"
        st.rerun()


def render_thank_you() -> None:
    progress(3)
    st.markdown("<div class='thank-you-mark'>✓</div><div class='hero-kicker'>Response received</div>", unsafe_allow_html=True)
    st.title("Thank you for sharing your view")
    st.write("Your response has been recorded. Your participation in this shopping activity is now complete.")
    st.info("You may now close this page.")


def main() -> None:
    st.set_page_config(page_title="SoundX Shopping Activity", page_icon="🎧", layout="centered", initial_sidebar_state="collapsed")
    st.markdown("""<style>
    .stApp {background:radial-gradient(circle at 15% 0%,#e9f8ef 0,transparent 27%),#fbfcfa;color:#15251b}.block-container{max-width:790px;padding:3.5rem 2rem 4rem}.brand{color:#17251c;font-size:.9rem;font-weight:850;letter-spacing:.1em;margin-bottom:3.6rem}.brand span{color:#2c9b60;font-weight:650}.hero-kicker{color:#16834b;font-size:.78rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;margin-bottom:.55rem}h1{color:#16261b;font-size:clamp(2.1rem,5vw,3.35rem)!important;line-height:1.08;letter-spacing:-.045em;margin-bottom:.8rem}.feature-row{display:flex;gap:1px;background:#dfe8e1;border:1px solid #dfe8e1;border-radius:14px;overflow:hidden;margin:2rem 0}.feature-row div{flex:1;background:rgba(255,255,255,.76);padding:1rem}.feature-row b{color:#16834b;font-size:1.1rem}.feature-row span{color:#5b675f;font-size:.83rem}[data-testid='stForm']{background:#fff;border:1px solid #e2e9e4;box-shadow:0 12px 30px rgba(23,54,34,.05);border-radius:18px;padding:1.4rem}.section-heading{color:#1a2b20;font-size:1.2rem;font-weight:750;margin:2.2rem 0 .3rem;padding-top:1.6rem;border-top:1px solid #e8eee9}.section-heading:first-child{border-top:0;padding-top:0;margin-top:0}.question-label{font-weight:650;color:#1a2b20;margin:1.35rem 0 .25rem}.scale-labels{display:flex;justify-content:space-between;color:#718075;font-size:.75rem;margin:-.35rem 0 .5rem}.quiet-note{color:#627067;font-size:.88rem;text-align:center;margin:.8rem 0 1.4rem}.thank-you-mark{background:#18864d;color:#fff;width:58px;height:58px;border-radius:50%;display:grid;place-items:center;font-size:1.8rem;margin-bottom:1.4rem}.stButton>button{background:#16834b;border:none;border-radius:10px;font-weight:750;min-height:3rem}.stButton>button:hover{background:#0e6738}[data-testid='stProgressBar']>div>div{background:#16834b}</style>""", unsafe_allow_html=True)
    initialise_session()
    {"welcome": render_welcome, "offer": render_offer, "survey": render_survey, "thank_you": render_thank_you}[st.session_state.page]()


if __name__ == "__main__":
    main()

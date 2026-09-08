"""Blinded, behavioural A/B study of discount framing."""
from __future__ import annotations

import secrets
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
ADS = {"A": BASE_DIR / "Version 1.png", "B": BASE_DIR / "Version 2.png"}

try:
    GOOGLE_SHEETS_URL = st.secrets["google_sheets"]["web_app_url"]
    GOOGLE_SHEETS_KEY = st.secrets["google_sheets"]["api_key"]
except Exception:
    GOOGLE_SHEETS_URL, GOOGLE_SHEETS_KEY = "", ""


def initialise_session() -> None:
    defaults = {
        "page": "welcome", "respondent_id": None, "participant_id": "", "assigned_group": None,
        "ad_shown_at": None, "decision": None, "decision_time_seconds": None,
        "add_to_cart": None, "checkout": None, "response_saved": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def begin_experiment(participant_id: str) -> None:
    st.session_state.respondent_id = f"R-{uuid.uuid4().hex[:8].upper()}"
    st.session_state.participant_id = participant_id.strip()
    st.session_state.assigned_group = secrets.choice(("A", "B"))
    for key in ("ad_shown_at", "decision", "decision_time_seconds", "add_to_cart", "checkout"):
        st.session_state[key] = None
    st.session_state.response_saved = False
    st.session_state.page = "offer"


def save_response(record: dict) -> tuple[bool, str]:
    if not GOOGLE_SHEETS_URL or not GOOGLE_SHEETS_KEY:
        return False, "The Google Sheet connection has not been configured yet."
    try:
        response = requests.post(GOOGLE_SHEETS_URL, json={**record, "api_key": GOOGLE_SHEETS_KEY}, timeout=20)
        response.raise_for_status()
        if response.json().get("ok") is not True:
            return False, "The response could not be saved. Please try again."
    except (requests.RequestException, ValueError) as error:
        return False, f"Could not save your response: {error}"
    return True, ""


def rating(question: str, key: str, low: str, high: str) -> int:
    st.markdown(f"<div class='question'>{question}</div>", unsafe_allow_html=True)
    result = st.radio(question, range(1, 8), index=None, horizontal=True, key=key, label_visibility="collapsed")
    st.markdown(f"<div class='scale'><span>{low}</span><span>{high}</span></div>", unsafe_allow_html=True)
    return result


def render_welcome() -> None:
    st.markdown("<div class='brand'>SOUNDX <span>SHOPPING LAB</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='eyebrow'>A short shopping activity</div>", unsafe_allow_html=True)
    st.title("Discover your next sound experience")
    st.write("Imagine you are browsing online and find a product offer. Please view it and respond as you normally would when shopping online.")
    st.markdown("<div class='steps'><div><b>01</b><br>View an offer</div><div><b>02</b><br>Make a choice</div><div><b>03</b><br>Share your view</div></div>", unsafe_allow_html=True)
    with st.form("start", border=False):
        participant_id = st.text_input("Participant ID (optional)", placeholder="For example, P001")
        st.caption("Takes about two minutes. Please complete this independently.")
        if st.form_submit_button("Start shopping activity  →", type="primary", use_container_width=True):
            begin_experiment(participant_id)
            st.rerun()


def render_offer() -> None:
    image_path = ADS[st.session_state.assigned_group]
    if not image_path.exists():
        st.error("The assigned product image is unavailable. Check that Version 1.png and Version 2.png are in GitHub.")
        st.stop()
    if st.session_state.ad_shown_at is None:
        st.session_state.ad_shown_at = time.perf_counter()

    st.progress(1 / 3, text="Step 1 of 3")
    st.markdown("<div class='eyebrow'>Your selected offer</div>", unsafe_allow_html=True)
    st.title("A closer look")
    st.write("Imagine this product appeared while you were shopping online.")
    st.image(str(image_path), use_container_width=True)
    st.markdown("<div class='note'>What would you like to do with this offer?</div>", unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        add_clicked = st.button("🛒  ADD TO CART", type="primary", use_container_width=True, disabled=st.session_state.decision is not None)
    with right:
        not_clicked = st.button("NOT INTERESTED", use_container_width=True, disabled=st.session_state.decision is not None)

    if add_clicked or not_clicked:
        st.session_state.decision = "ADD_TO_CART" if add_clicked else "NOT_INTERESTED"
        st.session_state.add_to_cart = "YES" if add_clicked else "NO"
        st.session_state.decision_time_seconds = round(time.perf_counter() - st.session_state.ad_shown_at, 3)
        st.session_state.checkout = None if add_clicked else "NOT_APPLICABLE"
        st.session_state.page = "cart" if add_clicked else "survey"
        st.rerun()


def render_cart() -> None:
    st.progress(2 / 3, text="Step 2 of 3")
    st.markdown("<div class='eyebrow'>Your cart</div>", unsafe_allow_html=True)
    st.title("Ready when you are")
    st.markdown("""<div class='cart-card'>
    <div><b>SoundX Wireless Headphones</b><br><span>Bluetooth 5.3 · 1-year warranty</span></div>
    <div class='price'><s>₹2,500</s> <strong>₹2,000</strong></div>
    </div>""", unsafe_allow_html=True)
    st.caption("This is a simulated shopping activity. No payment or financial information will be requested.")
    if st.button("PROCEED TO CHECKOUT  →", type="primary", use_container_width=True):
        st.session_state.checkout = "YES"
        st.session_state.page = "survey"
        st.rerun()
    if st.button("Continue without checkout", use_container_width=True):
        st.session_state.checkout = "NO"
        st.session_state.page = "survey"
        st.rerun()


def build_record(q1: int, q2: int, q3: int, attractiveness: int, recall: str, clarity: int, frequency: str, importance: int) -> dict:
    return {
        "respondent_id": st.session_state.respondent_id,
        "participant_id": st.session_state.participant_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "assigned_group": st.session_state.assigned_group,
        "decision": st.session_state.decision,
        "decision_time_seconds": st.session_state.decision_time_seconds,
        "add_to_cart": st.session_state.add_to_cart,
        "checkout": st.session_state.checkout,
        "purchase_intention_q1": q1,
        "purchase_intention_q2": q2,
        "purchase_intention_q3": q3,
        "purchase_intention_index": round((q1 + q2 + q3) / 3, 2),
        "offer_attractiveness": attractiveness,
        "discount_communication": recall,
        "discount_clarity": clarity,
        "online_shopping_frequency": frequency,
        "discount_importance": importance,
    }


def render_survey() -> None:
    st.progress(2 / 3, text="Step 2 of 3")
    st.markdown("<div class='eyebrow'>Your view</div>", unsafe_allow_html=True)
    st.title("A few quick questions")
    st.write("There are no right or wrong answers. Please respond based on the offer you just viewed.")
    with st.form("survey", border=False):
        st.markdown("<div class='section'>Purchase intention</div>", unsafe_allow_html=True)
        q1 = rating("How likely are you to purchase this product?", "q1", "1 · Very unlikely", "7 · Very likely")
        q2 = rating("How likely are you to consider purchasing this product?", "q2", "1 · Very unlikely", "7 · Very likely")
        q3 = rating("How likely are you to choose this offer over similar offers?", "q3", "1 · Very unlikely", "7 · Very likely")
        attractiveness = rating("How attractive did you find this offer?", "attractiveness", "1 · Not at all attractive", "7 · Extremely attractive")
        st.markdown("<div class='section'>About the offer</div>", unsafe_allow_html=True)
        recall = st.radio("How was the discount communicated?", ["Percentage discount", "Rupee amount saved", "I do not remember"], index=None, horizontal=True)
        clarity = rating("How clearly was the discount communicated?", "clarity", "1 · Not at all clear", "7 · Extremely clear")
        st.markdown("<div class='section'>Shopping habits</div>", unsafe_allow_html=True)
        frequency = st.select_slider("How often do you shop online?", ["Rarely", "Occasionally", "Monthly", "Weekly", "Several times a week"], value=None)
        importance = rating("How important are discounts when you shop online?", "importance", "1 · Not important", "7 · Extremely important")
        submitted = st.form_submit_button("Submit response  →", type="primary", use_container_width=True)

    if submitted:
        answers = [q1, q2, q3, attractiveness, recall, clarity, frequency, importance]
        if any(answer is None for answer in answers):
            st.error("Please complete every question before submitting.")
            return
        saved, message = save_response(build_record(q1, q2, q3, attractiveness, recall, clarity, frequency, importance))
        if not saved:
            st.error(message)
            return
        st.session_state.response_saved = True
        st.session_state.page = "thank_you"
        st.rerun()


def render_thank_you() -> None:
    st.progress(1.0, text="Step 3 of 3")
    st.markdown("<div class='tick'>✓</div><div class='eyebrow'>Response received</div>", unsafe_allow_html=True)
    st.title("Thank you")
    st.write("Your response has been recorded. Your participation is complete.")
    st.info("You may now close this page.")


def main() -> None:
    st.set_page_config(page_title="SoundX Shopping Activity", page_icon="🎧", layout="centered", initial_sidebar_state="collapsed")
    st.markdown("""<style>
    .stApp{background:radial-gradient(circle at 15% 0,#e9f8ef 0,transparent 28%),#fbfcfa;color:#17251c}.block-container{max-width:790px;padding:3.5rem 2rem 4rem}.brand{font-size:.88rem;font-weight:850;letter-spacing:.1em;margin-bottom:3.6rem}.brand span,.eyebrow{color:#16834b}.eyebrow{font-size:.76rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;margin-bottom:.55rem}h1{color:#16261b;font-size:clamp(2.1rem,5vw,3.2rem)!important;letter-spacing:-.04em}.steps{display:flex;gap:1px;background:#dfe8e1;border:1px solid #dfe8e1;border-radius:14px;overflow:hidden;margin:2rem 0}.steps div{flex:1;background:#fff;padding:1rem;color:#607067;font-size:.83rem}.steps b{color:#16834b;font-size:1.1rem}.note{text-align:center;color:#627067;margin:1.2rem 0}.cart-card{background:#fff;border:1px solid #e0e9e2;border-radius:14px;padding:1.35rem;display:flex;justify-content:space-between;align-items:center;margin:1.5rem 0}.cart-card span,.price s{color:#6d7970}.price strong{font-size:1.5rem;margin-left:.5rem}.section{font-size:1.15rem;font-weight:750;border-top:1px solid #e8eee9;padding-top:1.5rem;margin-top:2rem}.section:first-child{border-top:0;padding-top:0;margin-top:0}.question{font-weight:650;margin:1.25rem 0 .3rem}.scale{display:flex;justify-content:space-between;color:#718075;font-size:.75rem;margin:-.35rem 0 .5rem}.tick{width:58px;height:58px;border-radius:50%;display:grid;place-items:center;background:#18864d;color:white;font-size:1.8rem;margin-bottom:1.4rem}[data-testid='stForm']{background:white;border:1px solid #e2e9e4;border-radius:18px;padding:1.4rem}.stButton>button{background:#16834b;border:0;border-radius:10px;font-weight:750;min-height:3rem}.stButton>button:hover{background:#0e6738}[data-testid='stProgressBar']>div>div{background:#16834b}</style>""", unsafe_allow_html=True)
    initialise_session()
    {"welcome": render_welcome, "offer": render_offer, "cart": render_cart, "survey": render_survey, "thank_you": render_thank_you}[st.session_state.page]()


if __name__ == "__main__":
    main()

"""Blinded behavioural A/B shopping experience for discount framing."""
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
        "add_to_cart": None, "checkout": None, "saved": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def start() -> None:
    st.session_state.respondent_id = f"R-{uuid.uuid4().hex[:8].upper()}"
    st.session_state.assigned_group = secrets.choice(("A", "B"))
    for key in ("ad_shown_at", "decision", "decision_time_seconds", "add_to_cart", "checkout"):
        st.session_state[key] = None
    st.session_state.saved = False
    st.session_state.page = "offer"


def record() -> dict:
    return {
        "respondent_id": st.session_state.respondent_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "assigned_group": st.session_state.assigned_group,
        "decision": st.session_state.decision,
        "decision_time_seconds": st.session_state.decision_time_seconds,
        "add_to_cart": st.session_state.add_to_cart,
        "checkout": st.session_state.checkout,
    }


def save() -> tuple[bool, str]:
    if not GOOGLE_SHEETS_URL or not GOOGLE_SHEETS_KEY:
        return False, "The Google Sheet connection has not been configured yet."
    try:
        response = requests.post(GOOGLE_SHEETS_URL, json={**record(), "api_key": GOOGLE_SHEETS_KEY}, timeout=20)
        response.raise_for_status()
        if response.json().get("ok") is not True:
            return False, "We could not save this response. Please try again."
    except (requests.RequestException, ValueError) as error:
        return False, f"Could not save your response: {error}"
    st.session_state.saved = True
    return True, ""


def finish() -> None:
    saved, message = save()
    if saved:
        st.session_state.page = "thank_you"
        st.rerun()
    st.error(message)


def header() -> None:
    st.markdown("""<div class='topbar'><div class='logo'><span class='logo-mark'>〰</span> SOUND<span>X</span></div><div class='secure'>◉ SECURE SHOPPING</div></div>""", unsafe_allow_html=True)


def render_welcome() -> None:
    header()
    st.markdown("<div class='hero-pill'>✦ &nbsp; CURATED FOR YOUR LISTENING</div>", unsafe_allow_html=True)
    st.title("Find your sound.<br>Make it yours.")
    st.markdown("<p class='lead'>Take a quick look at a product selected for you. Shop just as you normally would.</p>", unsafe_allow_html=True)
    st.markdown("""<div class='trust-row'>
    <div><b>◷</b><span>Less than<br><strong>1 minute</strong></span></div>
    <div><b>◈</b><span>Your choice is<br><strong>private</strong></span></div>
    <div><b>✓</b><span>No payment<br><strong>required</strong></span></div>
    </div>""", unsafe_allow_html=True)
    st.markdown("<div class='launch-space'></div>", unsafe_allow_html=True)
    if st.button("EXPLORE THE OFFER  →", type="primary", use_container_width=True):
        start()
        st.rerun()
    st.markdown("<div class='footer-note'>By continuing, you are participating in a short shopping activity.</div>", unsafe_allow_html=True)


def render_offer() -> None:
    header()
    image = ADS[st.session_state.assigned_group]
    if not image.exists():
        st.error("Product image unavailable. Check that Version 1.png and Version 2.png are uploaded to GitHub.")
        st.stop()
    if st.session_state.ad_shown_at is None:
        st.session_state.ad_shown_at = time.perf_counter()

    st.markdown("<div class='breadcrumb'>HOME <span>›</span> AUDIO <span>›</span> HEADPHONES</div>", unsafe_allow_html=True)
    st.image(str(image), use_container_width=True)
    st.markdown("<div class='choice-title'>YOUR SHOPPING CHOICE</div><div class='choice-copy'>What would you like to do with this item?</div>", unsafe_allow_html=True)
    left, right = st.columns(2, gap="small")
    with left:
        cart = st.button("🛒  ADD TO CART", type="primary", use_container_width=True)
    with right:
        no = st.button("⌁  NOT INTERESTED", use_container_width=True)
    if cart or no:
        st.session_state.decision = "ADD_TO_CART" if cart else "NOT_INTERESTED"
        st.session_state.add_to_cart = "YES" if cart else "NO"
        st.session_state.checkout = None if cart else "NOT_APPLICABLE"
        st.session_state.decision_time_seconds = round(time.perf_counter() - st.session_state.ad_shown_at, 3)
        if cart:
            st.session_state.page = "cart"
            st.rerun()
        finish()


def render_cart() -> None:
    header()
    st.markdown("<div class='cart-kicker'>🛒 &nbsp; YOUR CART</div>", unsafe_allow_html=True)
    st.title("One great choice.")
    st.markdown("""<div class='cart-card'>
      <div class='cart-icon'>🎧</div>
      <div class='cart-info'><b>SoundX Wireless Headphones</b><span>Premium sound · 1-year warranty</span><div><s>₹2,500</s> <strong>₹2,000</strong></div></div>
    </div>""", unsafe_allow_html=True)
    st.markdown("""<div class='benefits'><span>✓ Free delivery</span><span>✓ Secure checkout</span><span>✓ Easy returns</span></div>""", unsafe_allow_html=True)
    st.markdown("<div class='simulated'>✦ This is a simulated store. No payment will be requested.</div>", unsafe_allow_html=True)
    if st.button("PROCEED TO CHECKOUT  →", type="primary", use_container_width=True):
        st.session_state.checkout = "YES"
        finish()
    if st.button("KEEP BROWSING", use_container_width=True):
        st.session_state.checkout = "NO"
        finish()


def render_thank_you() -> None:
    header()
    st.markdown("<div class='done-icon'>✓</div><div class='hero-pill'>SHOPPING ACTIVITY COMPLETE</div>", unsafe_allow_html=True)
    st.title("Thanks for stopping by.")
    st.markdown("<p class='lead'>Your shopping choice has been recorded. You may now close this page.</p>", unsafe_allow_html=True)
    st.markdown("<div class='done-line'></div><div class='footer-note'>SOUNDX · Tune into excellence</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="SoundX", page_icon="🎧", layout="centered", initial_sidebar_state="collapsed")
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,600&display=swap');
    .stApp{background:#f7f8f5;color:#18221f;font-family:'DM Sans',sans-serif}.block-container{max-width:770px;padding:1.8rem 2rem 4rem}.topbar{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #dce4dd;padding:0 0 1.35rem;margin-bottom:2.8rem}.logo{font-size:1rem;letter-spacing:.14em;font-weight:700}.logo span{color:#1d9b5b}.logo-mark{font-size:1.45rem;margin-right:.25rem}.secure{font-size:.65rem;letter-spacing:.1em;color:#668071;font-weight:700}.hero-pill,.cart-kicker{color:#16834b;font-size:.7rem;letter-spacing:.15em;font-weight:700}.hero-pill{display:inline-block;background:#e2f4e8;border-radius:20px;padding:.42rem .7rem}.stApp h1{font-family:'Playfair Display',serif;color:#15251b;font-size:clamp(2.8rem,7vw,4.6rem)!important;line-height:1.02;letter-spacing:-.055em;margin:.9rem 0 1rem}.lead{font-size:1.15rem;line-height:1.65;color:#59675f;max-width:560px}.trust-row{display:flex;gap:1px;border:1px solid #dbe6dd;background:#dbe6dd;border-radius:14px;overflow:hidden;margin:2.4rem 0}.trust-row div{display:flex;flex:1;gap:.65rem;background:#fff;padding:1rem;align-items:center}.trust-row b{color:#199158;font-size:1.4rem}.trust-row span{font-size:.74rem;color:#718078;line-height:1.35}.trust-row strong{color:#25342c}.launch-space{height:1.8rem}.footer-note{text-align:center;color:#8a968e;font-size:.72rem;letter-spacing:.03em;margin-top:1.2rem}.breadcrumb{font-size:.67rem;letter-spacing:.1em;color:#8a978e;font-weight:700;margin-bottom:1.2rem}.breadcrumb span{padding:0 .4rem;color:#32a366}.choice-title{font-weight:700;letter-spacing:.1em;font-size:.72rem;margin:1.8rem 0 .35rem}.choice-copy{color:#66746c;font-size:.9rem;margin-bottom:1rem}.cart-card{background:#fff;border:1px solid #dbe6dd;border-radius:18px;padding:1.3rem;display:flex;align-items:center;gap:1rem;margin:1.5rem 0 1rem;box-shadow:0 12px 25px rgba(29,73,45,.05)}.cart-icon{height:58px;width:58px;border-radius:14px;background:#e6f5eb;display:grid;place-items:center;font-size:1.8rem}.cart-info{display:grid;gap:.25rem}.cart-info b{font-size:1rem}.cart-info span,.cart-info s{font-size:.8rem;color:#7d8982}.cart-info strong{font-size:1.45rem;margin-left:.5rem}.benefits{display:flex;justify-content:space-around;gap:.4rem;color:#3d6550;font-size:.73rem;background:#eef7f1;border-radius:10px;padding:.75rem}.simulated{text-align:center;font-size:.78rem;color:#758279;margin:1.7rem 0}.done-icon{width:66px;height:66px;border-radius:50%;display:grid;place-items:center;color:#fff;background:#16834b;font-size:2rem;margin:5rem 0 1.4rem}.done-line{height:1px;background:#dce4dd;margin:3rem 0 0}[data-testid='stImage'] img{border-radius:18px;border:1px solid #e0e7e1}.stButton>button{border-radius:10px!important;min-height:3.15rem;border:1px solid #cedbd1!important;font-size:.8rem!important;letter-spacing:.05em;font-weight:700!important;background:#fff;color:#294534}.stButton>button[kind='primary']{background:#16834b!important;color:white!important;border-color:#16834b!important;box-shadow:0 8px 18px rgba(22,131,75,.16)}.stButton>button:hover{transform:translateY(-1px);border-color:#16834b!important}</style>""", unsafe_allow_html=True)
    initialise_session()
    {"welcome": render_welcome, "offer": render_offer, "cart": render_cart, "thank_you": render_thank_you}[st.session_state.page]()


if __name__ == "__main__":
    main()

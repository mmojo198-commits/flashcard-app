import streamlit as st
import pandas as pd
import json
from pathlib import Path
import random

# --- Page Config ---
st.set_page_config(
    page_title="Jomin's Flashcard App",
    page_icon="brain",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Session State ---
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = []
if 'original_flashcards' not in st.session_state:
    st.session_state.original_flashcards = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'file_loaded' not in st.session_state:
    st.session_state.file_loaded = False
if 'app_title' not in st.session_state:
    st.session_state.app_title = "Flashcard Review"
if 'font_size' not in st.session_state:
    st.session_state.font_size = 28
if 'transition' not in st.session_state:
    st.session_state.transition = "next"  # 'next' or 'prev'

# --- Custom CSS with Smooth Slide + 3D Flip ---
st.markdown("""
<style>
    .block-container { padding-top: 0rem !important; padding-bottom: 2rem !important; }
    header, #MainMenu, footer { visibility: hidden; height: 0 !important; }
    h1 { color: white !important; font-size: 36px !important; font-weight: 700 !important; margin: 0 !important; }

    .stApp {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 50%, #1e293b 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* === SLIDE TRANSITIONS === */
    @keyframes slideInRight {
        0% { transform: translateX(100%); opacity: 0; }
        100% { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideInLeft {
        0% { transform: translateX(-100%); opacity: 0; }
        100% { transform: translateX(0); opacity: 1; }
    }
    .slide-next { animation: slideInRight 0.5s cubic-bezier(0.4, 0, 0.2, 1) forwards; }
    .slide-prev { animation: slideInLeft 0.5s cubic-bezier(0.4, 0, 0.2, 1) forwards; }

    /* === 3D FLIP CARD === */
    .card-container {
        perspective: 1000px;
        margin: 40px auto;
        max-width: 700px;
        min-height: 400px;
    }
    .card-flipper {
        position: relative;
        width: 100%;
        height: 100%;
        min-height: 400px;
        transform-style: preserve-3d;
        transition: transform 0.6s cubic-bezier(0.4, 0.2, 0.2, 1);
    }
    .card-flipper.flipped {
        transform: rotateY(180deg);
    }
    .card-face {
        position: absolute;
        width: 100%;
        height: 100%;
        min-height: 400px;
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
        border-radius: 24px;
        padding: 60px 40px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        overflow-y: auto;
    }
    .card-front {
        background: linear-gradient(135deg, #2a344a 0%, #3e4a60 100%);
        border: 1px solid #475569;
    }
    .card-back {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border: 1px solid #059669;
        transform: rotateY(180deg);
    }

    /* Fix answer reveal timing */
    .card-back .card-text, .card-back .card-label {
        opacity: 0;
        transition: opacity 0s;
    }
    .flipped .card-back .card-text, .flipped .card-back .card-label {
        opacity: 1;
        transition: opacity 0.3s ease-in 0.3s;
    }

    .card-label {
        color: #e2e8f0;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 20px;
        font-weight: 600;
    }
    .card-text {
        color: white;
        line-height: 1.6;
        font-weight: 400;
        margin: 0;
        word-wrap: break-word;
        font-size: 28px;
    }

    /* Buttons */
    .stButton > button {
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: white !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        transition: all 0.3s !important;
    }
    .stButton > button:hover {
        background-color: #334155 !important;
        border-color: #64748b !important;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        background: #5c6b8f !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background: #6e7da6 !important;
    }

    /* Navigation arrows */
    .nav-button > button {
        border-radius: 50% !important;
        width: 56px !important;
        height: 56px !important;
        padding: 0 !important;
        font-size: 24px !important;
        background: #334155 !important;
        border: none !important;
    }

    /* Progress & inputs */
    [data-testid="stMetricValue"] { color: #a5b4fc !important; font-size: 24px !important; }
    .progress-container { max-width: 600px; margin: 0 auto; }
</style>
""", unsafe_allow_html=True)

# --- Functions ---
def load_flashcards(uploaded_file):
    file_extension = Path(uploaded_file.name).suffix.lower()
    df = None
    flashcards = []
    try:
        if file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(uploaded_file, header=None)
        elif file_extension == '.csv':
            df = pd.read_csv(uploaded_file, header=None)
        elif file_extension == '.json':
            uploaded_file.seek(0)
            data = json.load(uploaded_file)
            if isinstance(data, list) and all(isinstance(item, dict) and 'question' in item and 'answer' in item for item in data):
                return [{'question': str(item['question']).strip(), 'answer': str(item['answer']).strip()} for item in data]
            else:
                st.error("JSON must be list of {'question': ..., 'answer': ...} objects")
                return []

        if df is not None and df.shape[1] >= 2:
            for _, row in df.iterrows():
                q = str(row.iloc[0]).strip()
                a = str(row.iloc[1]).strip()
                if q and a and q.lower() != 'nan' and a.lower() != 'nan':
                    flashcards.append({'question': q, 'answer': a})
        return flashcards
    except Exception as e:
        st.error(f"Error: {e}")
        return []

def next_card():
    if st.session_state.current_index < len(st.session_state.flashcards) - 1:
        st.session_state.show_answer = False
        st.session_state.transition = "next"
        st.session_state.current_index += 1

def previous_card():
    if st.session_state.current_index > 0:
        st.session_state.show_answer = False
        st.session_state.transition = "prev"
        st.session_state.current_index -= 1

def toggle_answer():
    st.session_state.show_answer = not st.session_state.show_answer

def restart():
    st.session_state.show_answer = False
    st.session_state.current_index = 0
    st.session_state.transition = "next"

def shuffle_cards():
    if st.session_state.flashcards:
        random.shuffle(st.session_state.flashcards)
        st.session_state.show_answer = False
        st.session_state.current_index = 0
        st.session_state.transition = "next"

def reset_order():
    if st.session_state.original_flashcards:
        st.session_state.flashcards = st.session_state.original_flashcards.copy()
        restart()

# --- Main App ---
if not st.session_state.file_loaded or not st.session_state.flashcards:
    st.markdown("<h1 style='text-align: center;'>brain Jomin's Flashcard App</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 18px;'>Upload your deck (Excel, CSV, JSON) to start reviewing</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        subject = st.text_input("Deck Name (Optional)", "Flashcard Review")
        uploaded = st.file_uploader("Choose file", type=['xlsx', 'xls', 'csv', 'json'])
        if uploaded:
            st.session_state.app_title = subject if subject else "Flashcard Review"
            with st.spinner("Loading cards..."):
                cards = load_flashcards(uploaded)
                if cards:
                    st.session_state.flashcards = cards
                    st.session_state.original_flashcards = cards.copy()
                    st.session_state.file_loaded = True
                    st.session_state.current_index = 0
                    st.session_state.show_answer = False
                    st.session_state.transition = "next"
                    st.rerun()
else:
    current_card = st.session_state.flashcards[st.session_state.current_index]
    total = len(st.session_state.flashcards)
    current_num = st.session_state.current_index + 1

    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"<h1>brain {st.session_state.app_title}</h1>", unsafe_allow_html=True)
    with col2:
        if st.button("Upload New"):
            st.session_state.file_loaded = False
            st.rerun()

    # Navigation + Card
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        st.markdown("<div class='nav-button'>", unsafe_allow_html=True)
        st.button("←", on_click=previous_card, disabled=st.session_state.current_index == 0, key="prev")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        flip_class = "flipped" if st.session_state.show_answer else ""
        slide_class = "slide-next" if st.session_state.transition == "next" else "slide-prev"

        st.markdown(f"""
        <div class="card-container">
            <div class="card-flipper {flip_class} {slide_class}">
                <div class="card-face card-front">
                    <div class="card-label">QUESTION</div>
                    <p class="card-text" style="font-size: {st.session_state.font_size}px;">{current_card['question']}</p>
                </div>
                <div class="card-face card-back">
                    <div class="card-label">ANSWER</div>
                    <p class="card-text" style="font-size: {st.session_state.font_size}px;">{current_card['answer']}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Flip button
        c1, c2, c3 = st.columns([2, 1, 2])
        with c2:
            st.button("Flip Card", type="primary", on_click=toggle_answer, use_container_width=True, key="flip")

    with col3:
        st.markdown("<div class='nav-button'>", unsafe_allow_html=True)
        st.button("→", on_click=next_card, disabled=st.session_state.current_index == total - 1, key="next")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Footer Controls
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    with col1:
        c1, c2, c3 = st.columns(3)
        with c1: st.button("Order", on_click=reset_order)
        with c2: st.button("Shuffle", on_click=shuffle_cards)
        with c3: st.button("Reset", on_click=restart)
    
    with col2:
        progress = current_num / total
        st.progress(progress)
        st.markdown(f"<p style='text-align: center; color: white; font-size: 18px;'>Card {current_num} / {total} • {int(progress*100)}%</p>", unsafe_allow_html=True)
    
    with col3:
        jump = st.number_input("Jump to", 1, total, current_num, label_visibility="collapsed")
        if jump != current_num:
            st.session_state.current_index = jump - 1
            st.session_state.show_answer = False
            st.rerun()
    
    with col4:
        st.session_state.font_size = st.slider("Font Size", 16, 48, st.session_state.font_size, step=2, label_visibility="collapsed")

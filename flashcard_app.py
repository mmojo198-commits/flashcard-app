import streamlit as st
import pandas as pd
import io
import json
from pathlib import Path
import random

st.set_page_config(
    page_title="Jomin's Flashcard App",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS ---
st.markdown("""<style>
/* ... your CSS here, unchanged ... (You can use your exact CSS block) ... */
</style>""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = []
if 'original_flashcards' not in st.session_state: 
    st.session_state.original_flashcards = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if "previous_show_answer" not in st.session_state:
    st.session_state.previous_show_answer = False
if 'file_loaded' not in st.session_state:
    st.session_state.file_loaded = False
if 'app_title' not in st.session_state:
    st.session_state.app_title = "Flashcard Review"
if 'font_size' not in st.session_state:
    st.session_state.font_size = 28
if 'card_key' not in st.session_state:
    st.session_state.card_key = 0

# --- Data Loading Function ---
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
                flashcards = [{'question': str(item['question']).strip(), 'answer': str(item['answer']).strip()} for item in data]
                return flashcards
            else:
                st.error("JSON file must contain a list of objects with 'question' and 'answer'.")
                return []
        if df is not None:
            if df.shape[1] < 2:
                st.error("File must have at least two columns: Question and Answer.")
                return []
            questions_col = df.columns[0]
            answers_col = df.columns[1]
            for _, row in df.iterrows():
                question = str(row[questions_col]).strip()
                answer = str(row[answers_col]).strip()
                if question and answer and question.lower() != 'nan' and answer.lower() != 'nan':
                    flashcards.append({'question': question, 'answer': answer})
        return flashcards
    except Exception as e:
        st.error(f"Error loading {file_extension.upper()} file: {e}")
        return []

# --- Navigation & Control Functions (with Animation State) ---

def next_card():
    st.session_state.previous_show_answer = st.session_state.show_answer
    st.session_state.show_answer = False
    if st.session_state.current_index < len(st.session_state.flashcards) - 1:
        st.session_state.current_index += 1
        st.session_state.card_key += 1

def previous_card():
    st.session_state.previous_show_answer = st.session_state.show_answer
    st.session_state.show_answer = False
    if st.session_state.current_index > 0:
        st.session_state.current_index -= 1
        st.session_state.card_key += 1

def toggle_answer():
    st.session_state.previous_show_answer = st.session_state.show_answer
    st.session_state.show_answer = not st.session_state.show_answer

def restart():
    st.session_state.previous_show_answer = False
    st.session_state.current_index = 0
    st.session_state.show_answer = False
    st.session_state.card_key += 1

def shuffle_cards():
    if st.session_state.flashcards:
        random.shuffle(st.session_state.flashcards)
        st.session_state.previous_show_answer = False
        st.session_state.current_index = 0
        st.session_state.show_answer = False
        st.session_state.card_key += 1

def reset_order():
    if st.session_state.original_flashcards:
        st.session_state.flashcards = st.session_state.original_flashcards.copy()
        st.session_state.previous_show_answer = False
        st.session_state.current_index = 0
        st.session_state.show_answer = False
        st.session_state.card_key += 1

# --- Main App Layout ---

if not st.session_state.file_loaded or not st.session_state.flashcards:
    st.markdown("<h1 style='text-align: center;'>🧠 Jomin's Flashcard App</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 18px;'>Upload your study deck (Excel, CSV, or JSON) to begin your review.</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        subject_input = st.text_input("Enter Subject or Deck Name (Optional)", value="Flashcard Review", max_chars=50)
        uploaded_file = st.file_uploader("Choose a file", type=['xlsx', 'xls', 'csv', 'json'])
        if uploaded_file:
            st.session_state.app_title = subject_input if subject_input else "Flashcard Review"
            with st.spinner(f'Loading flashcards for {st.session_state.app_title}...'):
                flashcards = load_flashcards(uploaded_file)
                if flashcards:
                    st.session_state.flashcards = flashcards
                    st.session_state.original_flashcards = flashcards.copy()
                    st.session_state.file_loaded = True
                    st.session_state.current_index = 0
                    st.session_state.show_answer = False
                    st.session_state.card_key = 0
                    st.success(f"✅ Loaded {len(flashcards)} flashcards for: {st.session_state.app_title}!")
                    st.rerun()
                else:
                    st.error("❌ No valid flashcards found in the file!")

else:
    current_card = st.session_state.flashcards[st.session_state.current_index]
    total_cards = len(st.session_state.flashcards)
    current_num = st.session_state.current_index + 1

    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"<h1>🧠 {st.session_state.app_title}</h1>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='nav-button'>", unsafe_allow_html=True)
        if st.button("📤 Upload New", use_container_width=True, key="new_upload"):
            st.session_state.file_loaded = False
            st.session_state.flashcards = []
            st.session_state.original_flashcards = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 6, 1])

    with col1:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-button'>", unsafe_allow_html=True)
        st.button("←", on_click=previous_card, disabled=st.session_state.current_index == 0, key="prev")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        # --- Animate Flip if coming from Answer state ---
        if st.session_state.show_answer:
            flip_class = "flipped"
        elif st.session_state.previous_show_answer:
            # Render as flipped initially, then remove class using JS for animation
            flip_class = "flipped"
            # Inject a JS script that removes 'flipped' after render to trigger animation
            st.components.v1.html("""
            <script>
            setTimeout(function() {
                var el = window.parent.document.querySelector('.card-flipper');
                if (el) { el.classList.remove('flipped'); }
            }, 60);
            </script>
            """, height=0)
            st.session_state.previous_show_answer = False
        else:
            flip_class = ""

        st.markdown(f"""
        <div class="card-container" key="card-{st.session_state.card_key}">
            <div class="card-flipper {flip_class}">
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

        col_a, col_b, col_c = st.columns([2, 1, 2])
        with col_b:
            button_text = "🔄 Flip Card"
            if st.button(button_text, on_click=toggle_answer, use_container_width=True, key="flip-btn"):
                pass

    with col3:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-button'>", unsafe_allow_html=True)
        st.button("→", on_click=next_card, disabled=st.session_state.current_index == total_cards - 1, key="next")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    col1_footer, col2_footer, col3_footer, col4_footer = st.columns([1.5, 2.5, 1, 1])

    with col1_footer:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔢 Order", on_click=reset_order, use_container_width=True):
                pass
        with c2:
            if st.button("🔀 Shuffle", on_click=shuffle_cards, use_container_width=True):
                pass
        with c3:
            if st.button("⏮️ Reset", on_click=restart, use_container_width=True):
                pass

    with col2_footer:
        st.markdown("<div class='progress-container'>", unsafe_allow_html=True)
        progress = current_num / total_cards
        st.progress(progress)
        st.markdown(f"<p style='text-align: center; color: white; font-size: 18px; font-weight: 600; margin-top: 5px;'>Card {current_num} of {total_cards} | Completion: {int(progress * 100)}%</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col3_footer:
        st.markdown("<p style='text-align: center; color: #cbd5e1; font-size: 12px; margin-bottom: 2px; margin-top: 8px;'>Jump to:</p>", unsafe_allow_html=True)
        jump_card = st.number_input(
            "Jump to Card",
            min_value=1,
            max_value=total_cards,
            value=current_num,
            step=1,
            key=f"jump_input_{current_num}",
            label_visibility="collapsed"
        )
        if jump_card != current_num:
            st.session_state.current_index = jump_card - 1
            st.session_state.show_answer = False
            st.session_state.card_key += 1
            st.rerun()

    with col4_footer:
        st.markdown("<div class='font-size-slider' style='margin-top: 16px;'>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #cbd5e1; font-size: 12px; margin-bottom: 4px;'>Font Size</p>", unsafe_allow_html=True)
        st.session_state.font_size = st.slider(
            "Font Size",
            min_value=16,
            max_value=48,
            value=st.session_state.font_size,
            step=2,
            label_visibility="collapsed"
        )
        st.markdown("</div>", unsafe_allow_html=True)

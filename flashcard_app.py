import streamlit as st
import pandas as pd
import io
import json
from pathlib import Path
import random
import time

# --- Configuration and Styling ---

st.set_page_config(
    page_title="Jomin's Flashcard App",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for minimal top space + flip animations including "continuous forward flip"
st.markdown("""
<style>
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 2rem !important;
    }
    header, #MainMenu, footer {
        visibility: hidden;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    h1 {
        color: white !important;
        font-size: 36px !important;
        font-weight: 700 !important;
        margin-top: 0px !important;
        margin-bottom: 0px !important;
        padding-top: 0px !important;
    }
    .stApp {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 50%, #1e293b 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* 3D Flip Animation Styles */
    .card-container {
        perspective: 1000px;
        margin: 40px auto;
        max-width: 700px;
        min-height: 500px;
    }
    .card-flipper {
        position: relative;
        width: 100%;
        height: 100%;
        min-height: 500px;
        transform-style: preserve-3d;
        /* Default transition length (match in python sleep) */
        transition: transform 0.6s ease-in-out;
        transform: rotateY(0deg);
    }

    /* Normal flipped state (question -> answer shows 180deg) */
    .card-flipper.flipped {
        transform: rotateY(180deg);
    }

    /*
     Continuous forward-flip:
     When user is on the ANSWER (flipped = 180deg) and requests "next", we
     add a class that animates from 180deg -> 360deg (so it looks like it keeps spinning forward).
     The specificity below ensures .flip-continue takes precedence when present.
    */
    .card-flipper.flip-continue {
        transform: rotateY(360deg) !important;
    }

    /* Backwards continuous flip (if you want to implement reverse continuity later) */
    .card-flipper.flip-back-continue {
        transform: rotateY(-180deg) !important;
    }

    .card-face {
        position: absolute;
        width: 100%;
        height: 100%;
        min-height: 500px;
        max-height: 600px;
        backface-visibility: hidden;
        border-radius: 24px;
        padding: 40px 40px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
        text-align: center;
        overflow-y: auto;
        overflow-x: hidden;
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
    
    /* Mobile adjustments for taller cards */
    @media (max-width: 768px) {
        .card-container {
            min-height: 550px;
        }
        .card-flipper {
            min-height: 550px;
        }
        .card-face {
            min-height: 550px;
            max-height: 650px;
        }
    }
    
    .card-text {
        color: white;
        line-height: 1.6;
        font-weight: 400;
        margin: 0;
        word-wrap: break-word;
        overflow-wrap: break-word;
        max-width: 100%;
        padding: 20px 0;
    }
    .card-label {
        color: #e2e8f0;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 20px;
        font-weight: 600;
        flex-shrink: 0;
    }
    
    /* Custom scrollbar for card content */
    .card-face::-webkit-scrollbar {
        width: 8px;
    }
    .card-face::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    .card-face::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.3);
        border-radius: 10px;
    }
    .card-face::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.5);
    }
    
    .stButton > button {
        background: #4f46e5;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 500;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .stButton > button:hover {
        background: #6366f1;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .stButton > button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    .nav-button > button {
        background: #334155 !important;
        color: white !important;
        border: none !important;
        border-radius: 50% !important;
        width: 56px !important;
        height: 56px !important;
        min-width: 56px !important;
        padding: 0 !important;
        font-size: 24px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .nav-button > button:hover {
        background: #475569 !important;
    }
    .nav-button:hover > button {
        background: #475569 !important;
    }
    .stFileUploader {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 20px;
        border: 2px dashed #475569;
    }
    [data-testid="stMetricValue"] {
        color: #a5b4fc !important;
        font-size: 24px !important;
    }
    [data-testid="stMetricLabel"] {
        color: #cbd5e1 !important;
    }
    div[data-testid="column"] {
        gap: 0 !important;
    }
    
    /* Progress bar container - centered and constrained */
    .progress-container {
        max-width: 600px;
        margin: 0 auto;
    }
    .stProgress > div > div {
        max-width: 600px;
        margin: 0 auto;
    }
    
    /* Compact slider styling for font size control */
    .font-size-slider {
        font-size: 12px !important;
        color: #cbd5e1 !important;
    }
    .stSlider {
        margin: 0 !important;
        padding: 0 !important;
        max-width: 220px !important;
    }
    
    /* Jump to card input styling - CENTER ALIGNED */
    .stNumberInput {
        max-width: 150px !important;
        margin: 0 auto !important;
        display: flex !important;
        justify-content: center !important;
    }
    .stNumberInput > div {
        margin: 0 auto !important;
    }
    .stNumberInput > div > div > input {
        text-align: center !important;
        color: white !important;
        background: rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
        border: 1px solid #475569 !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---

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
# existing key used to force clean re-render in other flows
if 'card_key' not in st.session_state:
    st.session_state.card_key = 0

# New states for controlled animation transitions
if 'animating' not in st.session_state:
    st.session_state.animating = False
if 'animation_type' not in st.session_state:
    st.session_state.animation_type = None
if 'pending_next' not in st.session_state:
    st.session_state.pending_next = False

# --- Data Loading Function (FIXED) ---

def load_flashcards(uploaded_file):
    file_extension = Path(uploaded_file.name).suffix.lower()
    df = None
    flashcards = []

    try:
        if file_extension in ['.xlsx', '.xls']:
            # Added header=None to read the first row as data
            df = pd.read_excel(uploaded_file, header=None)
        elif file_extension == '.csv':
            # Added header=None to read the first row as data
            df = pd.read_csv(uploaded_file, header=None)
        elif file_extension == '.json':
            uploaded_file.seek(0)
            data = json.load(uploaded_file)
            if isinstance(data, list) and all(isinstance(item, dict) and 'question' in item and 'answer' in item for item in data):
                flashcards = [{'question': str(item['question']).strip(), 'answer': str(item['answer']).strip()} for item in data]
                return flashcards
            else:
                st.error("JSON file must contain a list of objects, each with 'question' and 'answer' keys.")
                return []
        
        if df is not None:
            # Ensure we have at least 2 columns
            if df.shape[1] < 2:
                st.error("File must have at least two columns: Question and Answer.")
                return []
            
            # Since header=None, columns are integers 0 and 1
            questions_col = df.columns[0]
            answers_col = df.columns[1]
            
            for _, row in df.iterrows():
                question = str(row[questions_col]).strip()
                answer = str(row[answers_col]).strip()
                
                # Basic validation to skip empty rows or 'nan' strings
                if question and answer and question.lower() != 'nan' and answer.lower() != 'nan':
                    flashcards.append({'question': question, 'answer': answer})
                    
        return flashcards
    except Exception as e:
        st.error(f"Error loading {file_extension.upper()} file: {e}")
        return []

# --- Navigation and Control Functions ---
# NOTE: we implement Option B: continuous forward flip from Answer -> Next Question
ANIMATION_DURATION = 0.6  # seconds (keep this synced with CSS transition)

def next_card_clicked():
    """Called by the Next button. Handles the Option B behavior:
       - If current view is ANSWER: animate forward (180->360deg) and then increment index,
         ensuring the new card appears on the QUESTION side without flashing its answer.
       - Otherwise: go to next card immediately.
    """
    # If already animating, ignore further clicks
    if st.session_state.animating:
        return

    # If we are currently showing the answer, perform continuous forward flip animation
    if st.session_state.show_answer:
        # Start animation: keep show_answer True (so CSS starts from flipped 180deg),
        # mark animating and set animation_type so render will include the extra class.
        st.session_state.animating = True
        st.session_state.animation_type = 'forward_continue'
        # Do NOT change card_key or index yet — we need the same DOM element to animate.
        st.rerun()
        return

    # Normal next movement when not showing answer
    if st.session_state.current_index < len(st.session_state.flashcards) - 1:
        st.session_state.current_index += 1
        st.session_state.show_answer = False
        st.session_state.card_key += 1  # Force clean re-render for other flows
        st.rerun()

def previous_card_clicked():
    # If animating, ignore
    if st.session_state.animating:
        return

    # For simplicity, previous while on ANSWER will just flip back to question and then move.
    # If you want continuous reverse behavior you can extend similarly.
    if st.session_state.show_answer:
        # flip back to question first (normal flip back), then mark pending_prev so we move after slight delay
        st.session_state.show_answer = False
        st.session_state.pending_prev = True
        # keep DOM same to allow the flip-back animation to run
        st.rerun()
        return

    if st.session_state.current_index > 0:
        st.session_state.current_index -= 1
        st.session_state.show_answer = False
        st.session_state.card_key += 1
        st.rerun()

def toggle_answer():
    if st.session_state.animating:
        return
    st.session_state.show_answer = not st.session_state.show_answer
    # Small flows don't need card_key bump — we want CSS flip to animate naturally
    st.rerun()

def restart():
    if st.session_state.animating:
        return
    st.session_state.current_index = 0
    st.session_state.show_answer = False
    st.session_state.card_key += 1
    st.rerun()

def shuffle_cards():
    if st.session_state.animating:
        return
    if st.session_state.flashcards:
        random.shuffle(st.session_state.flashcards)
        st.session_state.current_index = 0
        st.session_state.show_answer = False
        st.session_state.card_key += 1
        st.rerun()

def reset_order():
    if st.session_state.animating:
        return
    if st.session_state.original_flashcards:
        st.session_state.flashcards = st.session_state.original_flashcards.copy()
        st.session_state.current_index = 0
        st.session_state.show_answer = False
        st.session_state.card_key += 1
        st.rerun()

# --- Main App Layout ---

if not st.session_state.file_loaded or not st.session_state.flashcards:
    st.markdown("<h1 style='text-align: center;'>🧠 Jomin's Flashcard App</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 18px;'>Upload your study deck (Excel, CSV, or JSON) to begin your review.</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        subject_input = st.text_input(
            "Enter Subject or Deck Name (Optional)",
            value="Flashcard Review",
            max_chars=50,
            help="This name will appear as the main title of your session."
        )
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['xlsx', 'xls', 'csv', 'json'],
            help="Upload a file with Questions in the first column/field and Answers in the second."
        )
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
                    st.error("❌ No valid flashcards found in the file! Please check the file structure.")

else:
    current_card = st.session_state.flashcards[st.session_state.current_index]
    total_cards = len(st.session_state.flashcards)
    current_num = st.session_state.current_index + 1

    # Header with dynamic title
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"<h1>🧠 {st.session_state.app_title}</h1>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='nav-button'>", unsafe_allow_html=True)
        if st.button("📤 Upload New", use_container_width=True, key="new_upload"):
            # Reset everything to allow new upload
            st.session_state.file_loaded = False
            st.session_state.flashcards = []
            st.session_state.original_flashcards = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Main card area with navigation
    col1, col2, col3 = st.columns([1, 6, 1])

    with col1:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-button'>", unsafe_allow_html=True)
        disabled_prev = st.session_state.current_index == 0 or st.session_state.animating
        st.button("←", on_click=previous_card_clicked, disabled=disabled_prev, key="prev")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        # decide classes for card-flipper based on state
        classes = []
        if st.session_state.show_answer:
            classes.append("flipped")
        # If animating forward, add continuous flip class to animate 180->360
        if st.session_state.animating and st.session_state.animation_type == 'forward_continue':
            classes.append("flip-continue")
        flip_class = " ".join(classes)

        # 3D Flip Card Container with unique key to force clean re-render in other flows
        # We still keep card_key, but we MUST NOT change it at the start of the forward animation,
        # otherwise the DOM would be replaced and the animation wouldn't run.
        st.markdown(f"""
        <div class="card-container" key="card-{st.session_state.card_key}">
            <div class="card-flipper {flip_class}">
                <!-- Front of Card (Question) -->
                <div class="card-face card-front">
                    <div class="card-label">QUESTION</div>
                    <p class="card-text" style="font-size: {st.session_state.font_size}px;">{current_card['question']}</p>
                </div>
                <!-- Back of Card (Answer) -->
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
            # provide visual disabled when animating
            if st.button(button_text, 
                         on_click=toggle_answer, 
                         use_container_width=True,
                         disabled=st.session_state.animating,
                         key="flip-btn"):
                pass

    with col3:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-button'>", unsafe_allow_html=True)
        disabled_next = st.session_state.current_index == total_cards - 1 or st.session_state.animating
        # Wire to our next_card_clicked handler
        st.button("→", on_click=next_card_clicked, disabled=disabled_next, key="next")
        st.markdown("</div>", unsafe_allow_html=True)

    # If we started a forward continuous animation, wait for it to finish, then move to next card
    # (We intentionally block here for the animation duration so the CSS can run on the same DOM element)
    if st.session_state.animating and st.session_state.animation_type == 'forward_continue':
        # Sleep for the animation duration (slightly more to ensure completion)
        time.sleep(ANIMATION_DURATION + 0.05)

        # After animation completes: move to next card and ensure the new card shows QUESTION side
        if st.session_state.current_index < total_cards - 1:
            st.session_state.current_index += 1
        # reset animation flags
        st.session_state.animating = False
        st.session_state.animation_type = None
        # ensure next card renders with question visible (no flipped class) and force clean re-render
        st.session_state.show_answer = False
        st.session_state.card_key += 1
        st.rerun()

    # Handle pending_prev if we implemented "flip back then prev" pattern
    if getattr(st.session_state, "pending_prev", False):
        # allow flip-back animation to run
        time.sleep(ANIMATION_DURATION + 0.05)
        st.session_state.pending_prev = False
        if st.session_state.current_index > 0:
            st.session_state.current_index -= 1
        st.session_state.show_answer = False
        st.session_state.card_key += 1
        st.rerun()

    # Footer with progress and controls - CENTERED PROGRESS BAR
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1_footer, col2_footer, col3_footer, col4_footer = st.columns([1.5, 2.5, 1, 1])
    
    with col1_footer:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔢 Order", on_click=reset_order, use_container_width=True, help="Reset to original file order", disabled=st.session_state.animating):
                pass
        with c2:
            if st.button("🔀 Shuffle", on_click=shuffle_cards, use_container_width=True, help="Randomize cards", disabled=st.session_state.animating):
                pass
        with c3:
            if st.button("⏮️ Reset", on_click=restart, use_container_width=True, help="Go back to first card", disabled=st.session_state.animating):
                pass
                
    with col2_footer:
        # Wrapped in div for centering
        st.markdown("<div class='progress-container'>", unsafe_allow_html=True)
        progress = current_num / total_cards
        st.progress(progress)
        # Combined card count and completion percentage in one line
        st.markdown(f"<p style='text-align: center; color: white; font-size: 18px; font-weight: 600; margin-top: 5px;'>Card {current_num} of {total_cards} | Completion: {int(progress * 100)}%</p>", 
                    unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3_footer:
        st.markdown("<p style='text-align: center; color: #cbd5e1; font-size: 12px; margin-bottom: 2px; margin-top: 8px;'>Jump to:</p>", 
                    unsafe_allow_html=True)
        # Jump to card number input with dynamic key to force refresh
        jump_card = st.number_input(
            "Jump to Card",
            min_value=1,
            max_value=total_cards,
            value=current_num,
            step=1,
            key=f"jump_input_{current_num}",
            label_visibility="collapsed",
            help="Enter card number to jump directly",
            disabled=st.session_state.animating
        )
        if jump_card != current_num and not st.session_state.animating:
            st.session_state.current_index = jump_card - 1
            st.session_state.show_answer = False
            st.session_state.card_key += 1  # Force re-render
            st.rerun()
    
    with col4_footer:
        # Only Font Size slider
        st.markdown("<div class='font-size-slider' style='margin-top: 16px;'>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #cbd5e1; font-size: 12px; margin-bottom: 4px;'>Font Size</p>", unsafe_allow_html=True)
        st.session_state.font_size = st.slider(
            "Font Size",
            min_value=16,
            max_value=48,
            value=st.session_state.font_size,
            step=2,
            label_visibility="collapsed",
            disabled=st.session_state.animating
        )
        st.markdown("</div>", unsafe_allow_html=True)


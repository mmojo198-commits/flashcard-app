import streamlit as st
import pandas as pd
import io
import json
from pathlib import Path
import random

# --- Configuration and Styling ---

st.set_page_config(
    page_title="Jomin's Flashcard App",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
# Track animation direction ('next' or 'prev')
if 'anim_direction' not in st.session_state:
    st.session_state.anim_direction = 'next'

# --- Custom CSS ---
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
    
    /* --- ANIMATIONS START --- */
    
    @keyframes slideInRight {
        from { transform: translateX(50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .animate-next {
        animation: slideInRight 0.3s ease-out forwards;
    }
    
    .animate-prev {
        animation: slideInLeft 0.3s ease-out forwards;
    }
    
    /* --- ANIMATIONS END --- */

    /* 3D Flip Animation Styles */
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
        max-height: 500px;
        -webkit-backface-visibility: hidden;
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
        transform: rotateY(0deg);
        z-index: 2;
    }
    
    .card-back {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border: 1px solid #059669;
        transform: rotateY(180deg);
        z-index: 1;
    }

    /* --- SPOILER FIX: Hide answer text immediately when not flipped --- */
    .card-back .card-text, .card-back .card-label {
        opacity: 0;
        transition: opacity 0s; 
    }
    .flipped .card-back .card-text, .flipped .card-back .card-label {
        opacity: 1;
        transition: opacity 0.2s ease-in 0.2s; 
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
    
    /* Custom scrollbar */
    .card-face::-webkit-scrollbar { width: 8px; }
    .card-face::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
    .card-face::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.3); border-radius: 10px; }
    .card-face::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.5); }
    
    /* UI Elements & Buttons */
    .stButton > button {
        background: #4f46e5;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 20px;  /* Reduced padding for better fit */
        font-size: 15px;     /* Balanced font size */
        font-weight: 500;
        transition: all 0.3s ease;
        cursor: pointer;
        
        /* Fix for odd alignment/wrapping */
        white-space: nowrap;
        min-width: 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
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
    
    /* Navigation Arrow Buttons */
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
    }
    .nav-button > button:hover { background: #475569 !important; }
    
    /* File Uploader */
    .stFileUploader {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 20px;
        border: 2px dashed #475569;
    }
    
    /* Layout Adjustments */
    [data-testid="stMetricValue"] { color: #a5b4fc !important; font-size: 24px !important; }
    [data-testid="stMetricLabel"] { color: #cbd5e1 !important; }
    div[data-testid="column"] { gap: 0 !important; }
    
    .progress-container { max-width: 600px; margin: 0 auto; }
    .stProgress > div > div { max-width: 600px; margin: 0 auto; }
    
    .font-size-slider { font-size: 12px !important; color: #cbd5e1 !important; }
    .stSlider { margin: 0 !important; padding: 0 !important; max-width: 220px !important; }
    
    .stNumberInput { max-width: 150px !important; margin: 0 auto !important; display: flex !important; justify-content: center !important; }
    .stNumberInput > div { margin: 0 auto !important; }
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
                st.error("JSON file must contain a list of objects, each with 'question' and 'answer' keys.")
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

# --- Navigation and Control Functions ---

def next_card():
    if st.session_state.current_index < len(st.session_state.flashcards) - 1:
        st.session_state.show_answer = False
        st.session_state.anim_direction = 'next'
        st.session_state.current_index += 1

def previous_card():
    if st.session_state.current_index > 0:
        st.session_state.show_answer = False
        st.session_state.anim_direction = 'prev'
        st.session_state.current_index -= 1

def toggle_answer():
    st.session_state.show_answer = not st.session_state.show_answer

def restart():
    st.session_state.show_answer = False
    st.session_state.current_index = 0
    st.session_state.anim_direction = 'next'

def shuffle_cards():
    if st.session_state.flashcards:
        random.shuffle(st.session_state.flashcards)
        st.session_state.show_answer = False
        st.session_state.current_index = 0
        st.session_state.anim_direction = 'next'

def reset_order():
    if st.session_state.original_flashcards:
        st.session_state.flashcards = st.session_state.original_flashcards.copy()
        st.session_state.show_answer = False
        st.session_state.current_index = 0
        st.session_state.anim_direction = 'next'

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
        flip_class = "flipped" if st.session_state.show_answer else ""
        anim_class = "animate-next" if st.session_state.anim_direction == 'next' else "animate-prev"
        
        # Unique ID to trigger animation on re-render
        card_container_id = f"card-container-{st.session_state.current_index}"

        st.markdown(f"""
        <div id="{card_container_id}" class="card-container {anim_class}">
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
            if st.button("🔄 Flip Card", on_click=toggle_answer, use_container_width=True, key="flip-btn"):
                pass

    with col3:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-button'>", unsafe_allow_html=True)
        st.button("→", on_click=next_card, disabled=st.session_state.current_index == total_cards - 1, key="next")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Modified column ratios to give buttons more space
    col1_footer, col2_footer, col3_footer, col4_footer = st.columns([2, 2, 1, 1])
    
    with col1_footer:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔢 Order", on_click=reset_order, use_container_width=True): pass
        with c2:
            if st.button("🔀 Shuffle", on_click=shuffle_cards, use_container_width=True): pass
        with c3:
            if st.button("⏮️ Reset", on_click=restart, use_container_width=True): pass
                
    with col2_footer:
        st.markdown("<div class='progress-container'>", unsafe_allow_html=True)
        progress = current_num / total_cards
        st.progress(progress)
        st.markdown(f"<p style='text-align: center; color: white; font-size: 18px; font-weight: 600; margin-top: 5px;'>Card {current_num} of {total_cards} | Completion: {int(progress * 100)}%</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3_footer:
        st.markdown("<p style='text-align: center; color: #cbd5e1; font-size: 12px; margin-bottom: 2px; margin-top: 8px;'>Jump to:</p>", unsafe_allow_html=True)
        jump_card = st.number_input("Jump to Card", min_value=1, max_value=total_cards, value=current_num, step=1, key=f"jump_input_{current_num}", label_visibility="collapsed")
        if jump_card != current_num:
            st.session_state.anim_direction = 'next' if jump_card > current_num else 'prev'
            st.session_state.current_index = jump_card - 1
            st.session_state.show_answer = False
            st.rerun()
    
    with col4_footer:
        st.markdown("<div class='font-size-slider' style='margin-top: 16px;'>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #cbd5e1; font-size: 12px; margin-bottom: 4px;'>Font Size</p>", unsafe_allow_html=True)
        st.session_state.font_size = st.slider("Font Size", min_value=16, max_value=48, value=st.session_state.font_size, step=2, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

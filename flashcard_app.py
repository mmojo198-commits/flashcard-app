import streamlit as st
import pandas as pd
import json
import random
from pathlib import Path

# --- Configuration ---
st.set_page_config(
    page_title="Jomin's Flashcard App",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Session State Initialization ---
default_state = {
    'flashcards': [],
    'original_flashcards': [],
    'current_index': 0,
    'show_answer': False,
    'file_loaded': False,
    'app_title': "Flashcard Review",
    'font_size': 28
}

for key, val in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- Custom CSS (Preserved Exactly) ---
st.markdown("""
<style>
    .block-container { padding-top: 0rem !important; padding-bottom: 2rem !important; }
    header, #MainMenu, footer { visibility: hidden; height: 0 !important; margin: 0 !important; padding: 0 !important; }
    h1 { color: white !important; font-size: 36px !important; font-weight: 700 !important; margin: 0 !important; padding: 0 !important; }
    .stApp { background: linear-gradient(135deg, #1e293b 0%, #0f172a 50%, #1e293b 100%); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Animations */
    @keyframes flipIn { 0% { transform: rotateY(90deg); opacity: 0; } 100% { transform: rotateY(0deg); opacity: 1; } }
    .animate-flip { animation: flipIn 0.6s cubic-bezier(0.4, 0.2, 0.2, 1) forwards; }
    @keyframes buttonPress { 0% { transform: scale(0.96); } 50% { transform: scale(0.96); } 100% { transform: scale(1); } }

    /* 3D Card */
    .card-container { perspective: 1000px; margin: 40px auto; max-width: 700px; min-height: 400px; }
    .card-flipper { position: relative; width: 100%; height: 100%; min-height: 400px; transform-style: preserve-3d; transition: transform 0.6s cubic-bezier(0.4, 0.2, 0.2, 1); }
    .card-flipper.flipped { transform: rotateY(180deg); }
    .card-face { position: absolute; width: 100%; height: 100%; min-height: 400px; max-height: 500px; backface-visibility: hidden; -webkit-backface-visibility: hidden; border-radius: 24px; padding: 60px 40px; box-shadow: 0 20px 60px rgba(0,0,0,0.5); display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; overflow-y: auto; overflow-x: hidden; }
    .card-front { background: linear-gradient(135deg, #2a344a 0%, #3e4a60 100%); border: 1px solid #475569; transform: rotateY(0deg); z-index: 2; }
    .card-back { background: linear-gradient(135deg, #10b981 0%, #059669 100%); border: 1px solid #059669; transform: rotateY(180deg); z-index: 1; }
    
    /* Spoiler Fix */
    .card-back .card-text, .card-back .card-label { opacity: 0; transition: opacity 0s; }
    .flipped .card-back .card-text, .flipped .card-back .card-label { opacity: 1; transition: opacity 0.2s ease-in 0.2s; }
    
    .card-text { color: white; line-height: 1.6; font-weight: 400; margin: 0; word-wrap: break-word; overflow-wrap: break-word; max-width: 100%; }
    .card-label { color: #e2e8f0; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 20px; font-weight: 600; flex-shrink: 0; }
    .card-face::-webkit-scrollbar { width: 8px; }
    .card-face::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
    .card-face::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.3); border-radius: 10px; }

    /* Button Styling */
    .stButton > button { background-color: rgba(30, 41, 59, 0.8) !important; color: white !important; border: 1px solid #475569 !important; border-radius: 8px !important; padding: 10px 20px !important; font-size: 15px !important; font-weight: 500 !important; transition: background-color 0.3s, border-color 0.3s !important; }
    .stButton > button:hover { background-color: #334155 !important; border-color: #64748b !important; }
    .stButton > button:focus:not(:active) { animation: buttonPress 0.2s ease-out; }
    .stButton > button:active { transform: scale(0.96); transition: transform 0.1s; }
    
    div[data-testid="stButton"] > button[kind="primary"] { background: #5c6b8f !important; border: none !important; color: white !important; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important; }
    div[data-testid="stButton"] > button[kind="primary"]:hover { background: #6e7da6 !important; box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3) !important; }

    .nav-button > button { border-radius: 50% !important; width: 56px !important; height: 56px !important; padding: 0 !important; font-size: 24px !important; background: #334155 !important; border: none !important; }
    .stFileUploader { background: rgba(255,255,255,0.05); border-radius: 12px; padding: 20px; border: 2px dashed #475569; }
    
    [data-testid="stMetricValue"] { color: #a5b4fc !important; font-size: 24px !important; }
    [data-testid="stMetricLabel"] { color: #cbd5e1 !important; }
    div[data-testid="column"] { gap: 0 !important; }
    .progress-container { max-width: 600px; margin: 0 auto; }
    .stProgress > div > div { max-width: 600px; margin: 0 auto; }
    .font-size-slider { font-size: 12px !important; color: #cbd5e1 !important; }
    .stSlider { margin: 0 !important; padding: 0 !important; max-width: 220px !important; }
    .stNumberInput { max-width: 150px !important; margin: 0 auto !important; display: flex !important; justify-content: center !important; }
    .stNumberInput > div { margin: 0 auto !important; }
    .stNumberInput > div > div > input { text-align: center !important; color: white !important; background: rgba(255,255,255,0.1) !important; border-radius: 8px !important; border: 1px solid #475569 !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# --- Logic Functions ---

def load_flashcards(uploaded_file):
    ext = Path(uploaded_file.name).suffix.lower()
    try:
        if ext == '.json':
            data = json.load(uploaded_file)
            if isinstance(data, list) and all('question' in item and 'answer' in item for item in data):
                return [{'question': str(i['question']).strip(), 'answer': str(i['answer']).strip()} for i in data]
            st.error("Invalid JSON format."); return []

        # Pandas Loader for CSV/Excel
        if ext in ['.xlsx', '.xls']: df = pd.read_excel(uploaded_file, header=None)
        elif ext == '.csv': df = pd.read_csv(uploaded_file, header=None)
        else: return []

        if df.shape[1] < 2: st.error("File needs 2 columns."); return []
        
        # Optimize: Drop empties, convert to string, rename cols, export to dict
        df = df.iloc[:, :2].dropna()
        df.columns = ['question', 'answer']
        df = df.astype(str)
        # Filter out 'nan' strings if any remain
        df = df[(df['question'].str.lower() != 'nan') & (df['answer'].str.lower() != 'nan')]
        return df.to_dict('records')

    except Exception as e:
        st.error(f"Error loading file: {e}")
        return []

def change_card(step):
    new_idx = st.session_state.current_index + step
    if 0 <= new_idx < len(st.session_state.flashcards):
        st.session_state.current_index = new_idx
        st.session_state.show_answer = False

def toggle_answer():
    st.session_state.show_answer = not st.session_state.show_answer

def restart():
    st.session_state.update({'show_answer': False, 'current_index': 0})

def shuffle_cards():
    if st.session_state.flashcards:
        random.shuffle(st.session_state.flashcards)
        restart()

def reset_order():
    if st.session_state.original_flashcards:
        st.session_state.flashcards = st.session_state.original_flashcards.copy()
        restart()

def new_upload():
    st.session_state.update({'file_loaded': False, 'flashcards': [], 'original_flashcards': []})

# --- Main App ---

if not st.session_state.file_loaded or not st.session_state.flashcards:
    st.markdown("<h1 style='text-align: center;'>🧠 Jomin's Flashcard App</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 18px;'>Upload your study deck (Excel, CSV, or JSON) to begin your review.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        subject_input = st.text_input("Enter Subject or Deck Name (Optional)", value="Flashcard Review", max_chars=50)
        uploaded_file = st.file_uploader("Choose a file", type=['xlsx', 'xls', 'csv', 'json'])
        
        if uploaded_file:
            st.session_state.app_title = subject_input if subject_input else "Flashcard Review"
            with st.spinner(f'Loading flashcards...'):
                flashcards = load_flashcards(uploaded_file)
                if flashcards:
                    st.session_state.flashcards = flashcards
                    st.session_state.original_flashcards = flashcards.copy() 
                    st.session_state.file_loaded = True
                    restart()
                    st.rerun()
                else:
                    st.error("❌ No valid flashcards found!")

else:
    # --- Flashcard Review Interface ---
    idx = st.session_state.current_index
    cards = st.session_state.flashcards
    current_card = cards[idx]
    total = len(cards)

    # Header
    col1, col2 = st.columns([4, 1])
    with col1: st.markdown(f"<h1>🧠 {st.session_state.app_title}</h1>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='nav-button'>", unsafe_allow_html=True)
        st.button("📤 Upload New", on_click=new_upload, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Card & Navigation
    col1, col2, col3 = st.columns([1, 6, 1])

    with col1: # Left Arrow
        st.markdown("<div style='height: 10px;'></div><div class='nav-button'>", unsafe_allow_html=True)
        st.button("←", on_click=change_card, args=(-1,), disabled=(idx == 0), key="prev")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2: # Card Area
        flip_class = "flipped" if st.session_state.show_answer else ""
        
        st.markdown(f"""
        <div id="card-container-{idx}" class="card-container animate-flip">
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
        
        c_a, c_b, c_c = st.columns([2, 1, 2])
        with c_b:
            st.button("🔄 Flip Card", type="primary", on_click=toggle_answer, use_container_width=True)

    with col3: # Right Arrow
        st.markdown("<div style='height: 10px;'></div><div class='nav-button'>", unsafe_allow_html=True)
        st.button("→", on_click=change_card, args=(1,), disabled=(idx == total - 1), key="next")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Footer Controls
    f_c1, f_c2, f_c3, f_c4 = st.columns([2, 2, 1, 1])
    
    with f_c1:
        b1, b2, b3 = st.columns(3)
        b1.button("🔢 Order", on_click=reset_order, use_container_width=True)
        b2.button("🔀 Shuffle", on_click=shuffle_cards, use_container_width=True)
        b3.button("⏮️ Reset", on_click=restart, use_container_width=True)
                
    with f_c2:
        st.markdown("<div class='progress-container'>", unsafe_allow_html=True)
        prog = (idx + 1) / total
        st.progress(prog)
        st.markdown(f"<p style='text-align: center; color: white; font-size: 18px; font-weight: 600; margin-top: 5px;'>Card {idx + 1} of {total} | Completion: {int(prog * 100)}%</p></div>", unsafe_allow_html=True)
    
    with f_c3:
        st.markdown("<p style='text-align: center; color: #cbd5e1; font-size: 12px; margin-bottom: 2px; margin-top: 8px;'>Jump to:</p>", unsafe_allow_html=True)
        jump_val = st.number_input("Jump", 1, total, idx + 1, step=1, key=f"jump_{idx}", label_visibility="collapsed")
        if jump_val != idx + 1:
            st.session_state.current_index = jump_val - 1
            st.session_state.show_answer = False
            st.rerun()
    
    with f_c4:
        st.markdown("<div class='font-size-slider' style='margin-top: 16px;'><p style='text-align: center; color: #cbd5e1; font-size: 12px; margin-bottom: 4px;'>Font Size</p>", unsafe_allow_html=True)
        st.session_state.font_size = st.slider("Font", 16, 48, st.session_state.font_size, 2, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

import streamlit as st
import pandas as pd
import json
import random

# --- Configuration ---
st.set_page_config(
    page_title="Jomin's Flashcards",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- CSS for 3D Flip Animation ---
st.markdown("""
<style>
    /* Card Container */
    .card-container {
        perspective: 1000px;
        width: 100%;
        height: 400px;
        margin: 0 auto;
    }
    
    /* The Flipper */
    .card-flipper {
        position: relative;
        width: 100%;
        height: 100%;
        transform-style: preserve-3d;
        transition: transform 0.6s cubic-bezier(0.4, 0.2, 0.2, 1);
    }
    
    /* Flip State */
    .card-flipper.flipped {
        transform: rotateY(180deg);
    }
    
    /* Front and Back Common Styles */
    .card-face {
        position: absolute;
        width: 100%;
        height: 100%;
        backface-visibility: hidden;
        -webkit-backface-visibility: hidden;
        border-radius: 20px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        overflow-y: auto;
    }
    
    /* Front Face */
    .card-front {
        background: linear-gradient(135deg, #2a344a 0%, #3e4a60 100%);
        color: white;
        transform: rotateY(0deg);
        z-index: 2;
    }
    
    /* Back Face */
    .card-back {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        transform: rotateY(180deg);
        z-index: 1;
    }

    /* Text Styling */
    .card-label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 15px;
        opacity: 0.7;
    }
    
    .card-text {
        text-align: center;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# --- State Management ---
default_state = {
    'flashcards': [],
    'original_flashcards': [],
    'current_index': 0,
    'show_answer': False,
    'file_loaded': False,
    'font_size': 28
}

for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Functions ---

def load_flashcards(uploaded_file):
    """Parses Excel, CSV, or JSON into a list of dictionaries."""
    flashcards = []
    try:
        filename = uploaded_file.name.lower()
        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file, header=None)
        elif filename.endswith('.csv'):
            df = pd.read_csv(uploaded_file, header=None)
        elif filename.endswith('.json'):
            data = json.load(uploaded_file)
            return [{'question': str(i['question']), 'answer': str(i['answer'])} for i in data]
        else:
            return []

        # Process DataFrame (Expects Col 0: Question, Col 1: Answer)
        if df is not None and df.shape[1] >= 2:
            df = df.dropna(subset=[0, 1]) # Remove empty rows
            flashcards = [{'question': str(row[0]), 'answer': str(row[1])} for _, row in df.iterrows()]
            
        return flashcards
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return []

def next_card():
    if st.session_state.current_index < len(st.session_state.flashcards) - 1:
        st.session_state.show_answer = False
        st.session_state.current_index += 1

def prev_card():
    if st.session_state.current_index > 0:
        st.session_state.show_answer = False
        st.session_state.current_index -= 1

def flip_card():
    st.session_state.show_answer = not st.session_state.show_answer

def shuffle_deck():
    random.shuffle(st.session_state.flashcards)
    st.session_state.current_index = 0
    st.session_state.show_answer = False

def reset_deck():
    st.session_state.flashcards = st.session_state.original_flashcards.copy()
    st.session_state.current_index = 0
    st.session_state.show_answer = False

# --- Sidebar Controls ---
with st.sidebar:
    st.header("⚙️ Controls")
    
    # File Uploader
    uploaded_file = st.file_uploader("Upload Deck", type=['xlsx', 'csv', 'json'])
    if uploaded_file:
        cards = load_flashcards(uploaded_file)
        if cards:
            st.session_state.flashcards = cards
            st.session_state.original_flashcards = cards.copy()
            st.session_state.file_loaded = True
            st.session_state.current_index = 0
            st.success(f"Loaded {len(cards)} cards!")
        else:
            st.error("Could not load cards.")

    if st.session_state.file_loaded:
        st.divider()
        st.session_state.font_size = st.slider("Font Size", 16, 48, 28)
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.button("🔀 Shuffle", on_click=shuffle_deck, use_container_width=True)
        with col_s2:
            st.button("↺ Reset", on_click=reset_deck, use_container_width=True)

# --- Main App ---

if not st.session_state.file_loaded:
    st.title("🧠 Jomin's Flashcards")
    st.info("👈 Please upload a CSV, Excel, or JSON file in the sidebar to start.")
    
    st.markdown("""
    **File Format Guide:**
    - **Excel/CSV:** Column A = Question, Column B = Answer (No headers needed).
    - **JSON:** A list of objects: `[{"question": "...", "answer": "..."}]`
    """)

else:
    # Progress
    total = len(st.session_state.flashcards)
    current = st.session_state.current_index + 1
    progress = current / total
    
    st.progress(progress)
    st.caption(f"Card {current} of {total}")

    # The Card
    card = st.session_state.flashcards[st.session_state.current_index]
    flip_class = "flipped" if st.session_state.show_answer else ""
    
    # HTML Card Rendering
    st.markdown(f"""
    <div class="card-container">
        <div class="card-flipper {flip_class}">
            <div class="card-face card-front">
                <div class="card-label">QUESTION</div>
                <div class="card-text" style="font-size: {st.session_state.font_size}px;">
                    {card['question']}
                </div>
            </div>
            <div class="card-face card-back">
                <div class="card-label">ANSWER</div>
                <div class="card-text" style="font-size: {st.session_state.font_size}px;">
                    {card['answer']}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation Controls (Below Card)
    st.markdown("<br>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c1:
        st.button("⬅️ Prev", on_click=prev_card, disabled=(st.session_state.current_index == 0), use_container_width=True)
    
    with c2:
        btn_label = "🔄 Flip to Question" if st.session_state.show_answer else "👀 Reveal Answer"
        type_btn = "secondary" if st.session_state.show_answer else "primary"
        st.button(btn_label, on_click=flip_card, type=type_btn, use_container_width=True)
        
    with c3:
        st.button("Next ➡️", on_click=next_card, disabled=(st.session_state.current_index == total - 1), use_container_width=True)

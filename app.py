import streamlit as st
from openai import OpenAI
import base64
from pathlib import Path
import os
import json
from datetime import datetime
from collections import defaultdict
import bcrypt
import io

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Pomocnik Językowy", layout="wide")

# --- KONFIGURACJA API I ŚCIEŻEK ---
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)
BASE_HISTORY_DIR = "user_histories"

# --- TWOJA LISTA JĘZYKÓW ---
languages = {
    "polski": "polski", "angielski": "angielski", "francuski": "francuski",
    "niemiecki": "niemiecki", "hiszpański": "hiszpański", "włoski": "włoski",
    "chiński": "chiński", "japoński": "japoński", "rosyjski": "rosyjski",
    "arabski": "arabski", "portugalski": "portugalski", "koreański": "koreański",
    "holenderski": "holenderski", "szwedzki": "szwedzki", "grecki": "grecki",
    "czeski": "czeski", "turecki": "turecki", "węgierski": "węgierski",
    "fiński": "fiński", "indonezyjski": "indonezyjski", "tajski": "tajski",
    "wietnamski": "wietnamski", "hebrajski": "hebrajski", "perski": "perski",
    "ukraiński": "ukraiński", "rumuński": "rumuński", "bułgarski": "bułgarski",
    "słowacki": "słowacki", "chorwacki": "chorwacki", "auto-wykrywanie": "auto-wykrywanie"
}

# --- FUNKCJE BAZY DANYCH ---
def get_user_history_path(username):
    user_dir = Path(BASE_HISTORY_DIR) / username
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / "history.json"

def load_history(username):
    history_path = get_user_history_path(username)
    try:
        if history_path.exists():
            with open(history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_history(username, history):
    history_path = get_user_history_path(username)
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def clear_history(username):
    history_path = get_user_history_path(username)
    if history_path.exists():
        os.remove(history_path)

# --- FUNKCJE POMOCNICZE ---
def img_to_bytes(img_path):
    try:
        img_bytes = Path(img_path).read_bytes()
        return base64.b64encode(img_bytes).decode()
    except FileNotFoundError:
        return ""

def translate_text(text, source_lang, target_lang, mode="translate"):
    if mode == "fix":
        system_instruction = f"Działasz jako profesjonalny edytor i tłumacz. Język docelowy: {target_lang}. Popraw błędy i wygeneruj naturalną wersję."
    elif mode == "explain":
        system_instruction = f"Jesteś nauczycielem języka {target_lang}. Przetłumacz i wyjaśnij słownictwo/gramatykę po polsku."
    else:
        system_instruction = f"Jesteś profesjonalnym tłumaczem z {source_lang} na {target_lang}."

    prompt_content = (
        f"{system_instruction}\n"
        "Format: 1. Tekst wynikowy\n2. Separator: ---\n3. Uwagi/Wyjaśnienia"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt_content}, {"role": "user", "content": text}],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Błąd: {e}"

def generate_audio(text):
    try:
        response = client.audio.speech.create(model="tts-1", voice="alloy", input=text)
        return response.content
    except Exception:
        return None

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

# --- LOGOWANIE ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("Logowanie")
    u_in = st.text_input("Nazwa użytkownika")
    p_in = st.text_input("Hasło", type="password")
    if st.button("Zaloguj"):
        users = st.secrets["users"]
        if u_in in users and verify_password(p_in, users[u_in]):
            st.session_state["logged_in"] = True
            st.session_state["username"] = u_in
            st.rerun()
        else:
            st.error("Błąd logowania!")
    st.stop()

# --- GŁÓWNA APLIKACJA ---
def main():
    # Inicjalizacja stanu sesji dla wszystkich pól
    if "input_text_val" not in st.session_state: st.session_state["input_text_val"] = ""
    if "source_lang_val" not in st.session_state: st.session_state["source_lang_val"] = "auto-wykrywanie"
    if "target_lang_val" not in st.session_state: st.session_state["target_lang_val"] = "angielski"
    if "translation_val" not in st.session_state: st.session_state["translation_val"] = ""
    if "analysis_val" not in st.session_state: st.session_state["analysis_val"] = ""

    st.markdown("""
        <style>
            div[data-testid="stTextArea"]:has(textarea[aria-label="Twój tekst:"]) textarea { background-color: #f0f7ff !important; border: 2px solid #007bff !important; }
            div[data-testid="stTextArea"]:has(textarea[aria-label="Twoje tłumaczenie:"]) textarea { background-color: #f6fff6 !important; border: 2px solid #28a745 !important; }
            div[data-testid="stTextArea"]:has(textarea[aria-label="Analiza i wyjaśnienia:"]) textarea { background-color: #fffaf0 !important; border: 2px solid #ff8c00 !important; }
        </style>
    """, unsafe_allow_html=True)

    username = st.session_state["username"]
    
    # Sidebar
    st.sidebar.header(f"Witaj, {username}")
    if st.sidebar.button("Wyloguj"):
        st.session_state.clear()
        st.rerun()
    st.sidebar.divider()

    # Logo
    encoded_image = img_to_bytes("logo.png")
    if encoded_image:
        st.markdown(f'<div style="display: flex; align-items: center; margin-bottom: 30px;"><img src="data:image/png;base64,{encoded_image}" width="80" style="margin-right: 20px;"><h1>POMOCNIK JĘZYKOWY PIONIERA</h1></div>', unsafe_allow_html=True)
    else:
        st.title("POMOCNIK JĘZYKOWY PIONIERA")

    # Historia
    history = load_history(username)
    st.sidebar.header("Twoja Historia")
    if history:
        if st.sidebar.button("🗑️ Wyczyść historię"):
            clear_history(username)
            st.rerun()
        
        for i, e in enumerate(reversed(history[-15:])):
            with st.sidebar.expander(f"📅 {e['timestamp']}"):
                st.write(f"**{e['source_lang']} ➔ {e['target_lang']}**")
                st.text(f"{e['original'][:60]}...")
                if st.sidebar.button(f"Otwórz wpis", key=f"hbtn_{i}"):
                    # PRZYWRACANIE WSZYSTKIEGO DO SESJI
                    st.session_state["input_text_val"] = e['original']
                    st.session_state["source_lang_val"] = e['source_lang']
                    st.session_state["target_lang_val"] = e['target_lang']
                    st.session_state["translation_val"] = e.get('translation_only', "")
                    st.session_state["analysis_val"] = e.get('analysis_only', "")
                    st.rerun()

    # Interfejs
    col1, col2 = st.columns(2)
    with col1:
        src_lang_list = list(languages.keys())
        s_idx = src_lang_list.index(st.session_state["source_lang_val"]) if st.session_state["source_lang_val"] in src_lang_list else 0
        src_l = st.selectbox("Źródło:", src_lang_list, index=s_idx)
        input_t = st.text_area("Twój tekst:", value=st.session_state["input_text_val"], height=250)

    with col2:
        tgt_lang_list = [l for l in languages.keys() if l != "auto-wykrywanie"]
        t_idx = tgt_lang_list.index(st.session_state["target_lang_val"]) if st.session_state["target_lang_val"] in tgt_lang_list else 0
        tgt_l = st.selectbox("Cel:", tgt_lang_list, index=t_idx)
        st.write("---")
        c1, c2, c3 = st.columns(3)
        b1, b2, b3 = c1.button("🚀 Tłumacz"), c2.button("✨ Popraw"), c3.button("📚 Wyjaśnij")

    # Logika przycisków
    if b1 or b2 or b3:
        if not input_t.strip():
            st.warning("Wpisz tekst!")
        else:
            mode = "explain" if b3 else ("fix" if b2 else "translate")
            with st.spinner("Przetwarzanie..."):
                res = translate_text(input_t, src_l, tgt_l, mode)
                translation, info = res.split("---", 1) if "---" in res else (res, "Brak uwag.")
                
                # Zapisujemy wynik do stanu sesji
                st.session_state["input_text_val"] = input_t
                st.session_state["source_lang_val"] = src_l
                st.session_state["target_lang_val"] = tgt_l
                st.session_state["translation_val"] = translation.strip()
                st.session_state["analysis_val"] = info.strip()

                # Zapis do historii (z rozbiciem na pola)
                history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source_lang": src_l, "target_lang": tgt_l,
                    "original": input_t,
                    "translation_only": translation.strip(),
                    "analysis_only": info.strip()
                })
                save_history(username, history)
                st.rerun()

    # WYŚWIETLANIE WYNIKÓW (jeśli są w sesji)
    if st.session_state["translation_val"]:
        st.divider()
        r1, r2 = st.columns(2)
        with r1:
            st.text_area("Twoje tłumaczenie:", value=st.session_state["translation_val"], height=300)
            audio_bytes = generate_audio(st.session_state["translation_val"])
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
                st.download_button(label="📥 Pobierz MP3", data=audio_bytes, file_name="audio.mp3", mime="audio/mp3")
        with r2:
            st.text_area("Analiza i wyjaśnienia:", value=st.session_state["analysis_val"], height=400)

if __name__ == "__main__":
    main()
import os, requests, streamlit as st

API_URL = os.environ.get("API_URL", "http://backend:8000")

st.title("Streamlit + FastAPI + PostgreSQL")

with st.form("add"):
    content = st.text_input("Nouvelle note")
    submitted = st.form_submit_button("Ajouter")
    if submitted and content.strip():
        r = requests.post(f"{API_URL}/notes", json={"content": content})
        if r.ok:
            st.success("Note ajoutée.")
        else:
            st.error(f"Erreur API: {r.text}")

st.subheader("Notes")
try:
    r = requests.get(f"{API_URL}/notes", timeout=5)
    if r.ok:
        for n in r.json():
            st.write(f"• #{n['id']} — {n['content']}")
    else:
        st.error("Impossible de récupérer les notes (API).")
except Exception as e:
    st.error(f"Connexion API échouée: {e}")
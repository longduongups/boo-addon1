# streamlit_app_dynamodb.py
import streamlit as st
import boto3
import pandas as pd
from decimal import Decimal
from datetime import datetime
import unicodedata
import re
from uuid import uuid4

# AWS DynamoDB setup
REGION = "eu-north-1"
dynamodb = boto3.resource("dynamodb", region_name=REGION)
MEASUREMENTS_TABLE = "BreastMeasurements"
PENDING_TABLE = "PendingMeasurements"

# --- Helpers ---
def sanitize_filename(name):
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^\w\-_.]", "_", name)
    return name

def upload_to_pending_table(email, filename):
    timestamp = datetime.utcnow().isoformat()
    item = {
        "email": email,
        "filename": filename,
        "status": "pending",
        "timestamp": timestamp
    }
    try:
        table = dynamodb.Table(PENDING_TABLE)
        table.put_item(Item=item)
        return True
    except Exception as e:
        st.error(f"❌ Erreur DynamoDB: {e}")
        return False

def load_all_emails():
    try:
        table = dynamodb.Table(MEASUREMENTS_TABLE)
        response = table.scan(ProjectionExpression="email")
        emails = set(item["email"] for item in response.get("Items", []))
        return sorted(emails)
    except Exception as e:
        st.error(f"❌ Erreur chargement emails : {e}")
        return []

def load_client_data(email):
    try:
        table = dynamodb.Table(MEASUREMENTS_TABLE)
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("email").eq(email)
        )
        items = response.get("Items", [])
        return pd.DataFrame(items).sort_values("timestamp", ascending=False) if items else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erreur chargement mesures : {e}")
        return pd.DataFrame()

# --- Interface ---
st.set_page_config(page_title="Mesures Poitrine - DynamoDB", layout="wide")
st.title("📊 Mesures Poitrine (DynamoDB)")

params = st.query_params
selected_email = params.get("email", [None])[0]

if not selected_email:
    st.subheader("👥 Choisir ou ajouter un utilisateur")
    emails = load_all_emails()
    selected = st.selectbox("Adresse email", emails)

    if st.button("📂 Voir les mesures") and selected:
        st.query_params["email"] = selected
        st.rerun()

    st.divider()

    st.subheader("➕ Ajouter un utilisateur + .obj")
    new_email = st.text_input("Nouvelle adresse email")
    uploaded_file = st.file_uploader("Fichier .obj", type=["obj"])

    if new_email and uploaded_file and st.button("📤 Enregistrer modèle"):
        filename = f"{uuid4().hex}_{sanitize_filename(uploaded_file.name)}"
        if upload_to_pending_table(new_email, filename):
            st.success("✅ Modèle et tâche enregistrés dans DynamoDB")
else:
    email = selected_email.strip().lower()
    df = load_client_data(email)

    if df.empty:
        st.warning("Aucune mesure trouvée pour cet utilisateur.")
        if st.button("⬅️ Retour"):
            st.query_params.clear()
            st.rerun()
        st.stop()

    row = df.iloc[0]
    st.subheader(f"👤 Mesures pour : {email}")
    st.markdown(f"*Dernière mesure :* `{row['timestamp'][:19]}`")

    c1, c2 = st.columns(2)
    with c1:
        st.metric("📏 Hauteur", f"{row['height_cm']} cm")
        st.metric("⬅️ Largeur gauche", f"{row['width_left_cm']} cm")
    with c2:
        st.metric("➡️ Largeur droite", f"{row['width_right_cm']} cm")
        st.metric("📦 Volume", f"{row['volume_cm3']} cm³")

    st.progress(int(float(row['bust_circumference_cm'])))
    st.progress(int(float(row['band_circumference_cm'])))

    st.markdown(f"**Type vertical :** `{row['vertical_type']}`")
    st.markdown(f"**Type horizontal :** `{row['horizontal_type']}`")

    if st.button("⬅️ Retour à la liste"):
        st.query_params.clear()
        st.rerun()

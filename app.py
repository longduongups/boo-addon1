import streamlit as st
import pandas as pd
from datetime import datetime
import unicodedata
import re
from uuid import uuid4
import boto3

import boto3
from datetime import datetime


REGION = "eu-north-1"
dynamodb = boto3.resource("dynamodb", region_name=REGION)

TABLE_MEASUREMENTS = "BreastMeasurements"
TABLE_PENDING = "PendingMeasurements"

REGION = "eu-north-1"
S3_BUCKET = "boo-models-test"

st.set_page_config(page_title="Accueil - Upload 3D", layout="wide")
st.title("📄 Uploader un modèle 3D & Visualiser des mesures")

# --- Fonctions utiles ---
def sanitize_filename(name):
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^\w\-_.]", "_", name)

def upload_to_storage(file_bytes, filename):
    try:
        s3 = boto3.client("s3", region_name=REGION)
        s3.put_object(Bucket=S3_BUCKET, Key=filename, Body=file_bytes)
        return True
    except Exception as e:
        st.error(f"Erreur S3 : {e}")
        return False
def record_pending_job(email, filename):
    item = {
        "email": email,
        "timestamp": datetime.utcnow().isoformat(),
        "filename": filename,
        "status": "pending"
    }
    try:
        table = dynamodb.Table(TABLE_PENDING)
        table.put_item(Item=item)
        return True
    except Exception as e:
        print(f"Erreur DynamoDB : {e}")
        return False


def get_existing_emails():
    try:
        table = dynamodb.Table(TABLE_MEASUREMENTS)
        response = table.scan(ProjectionExpression="email")
        emails = {item["email"] for item in response.get("Items", [])}
        return sorted(emails)
    except Exception as e:
        print(f"Erreur DynamoDB : {e}")
        return []


# --- Upload section ---
st.subheader("1️⃣ Uploader un fichier .obj")
email = st.text_input("Adresse email")
uploaded_file = st.file_uploader("Fichier .obj", type=["obj"])

if uploaded_file and email:
    filename = f"{uuid4().hex}_{sanitize_filename(uploaded_file.name)}"
    if st.button("Envoyer dans DynamoDB"):
        with st.spinner("Envoi en cours..."):
            success = upload_to_storage(uploaded_file.getvalue(), filename)
            if success and record_pending_job(email, filename):
                st.success("✅ Fichier et tâche enregistrés")
            else:
                st.error("❌ Échec de l’enregistrement")

st.divider()

# --- Visualisation section ---
st.subheader("2️⃣ Visualiser les mesures existantes")
emails = get_existing_emails()
if emails:
    selected_email = st.selectbox("Choisir un email :", emails)
    if st.button("Visualiser les mesures"):
        st.session_state["email"] = selected_email
        st.switch_page("pages/visualiser.py")

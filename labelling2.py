import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIG
# =========================
SHEET_NAME = "annotation_data"

# =========================
# GOOGLE SHEETS CONNECTION
# =========================
@st.cache_resource
def init_connection():

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = st.secrets["gcp_service_account"]

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=scope
    )

    client = gspread.authorize(creds)

    sheet = client.open(SHEET_NAME).sheet1

    return sheet

sheet = init_connection()

# =========================
# LOAD DATA
# =========================
@st.cache_data(show_spinner=False)
def load_data():
    return pd.read_csv("labeling_data.csv")

data = load_data()

# =========================
# GET RECORDS
# =========================
@st.cache_data(ttl=5)
def get_records():
    return sheet.get_all_records()

records = get_records()

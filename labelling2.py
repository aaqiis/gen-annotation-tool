import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =========================
# CONFIG
# =========================
SHEET_NAME = "annotation_data"
CREDENTIAL_FILE = "credentials.json"

# =========================
# GOOGLE SHEETS CONNECTION
# =========================
@st.cache_resource
def init_connection():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIAL_FILE, scope
    )
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

sheet = init_connection()

# =========================
# LOAD DATA
# =========================
@st.cache_data
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

record_index_map = {
    (str(r["id"]), r["annotator"]): i + 2
    for i, r in enumerate(records)
}

# =========================
# SESSION
# =========================
if "idx" not in st.session_state:
    st.session_state.idx = 0

if "annotator" not in st.session_state:
    st.session_state.annotator = ""

# =========================
# UI
# =========================
st.title("📊 Text Labeling Tool")

annotator_list = [
    "Pak Abrian",
    "Bu Jiphie"
]

annotator = st.selectbox(
    "Pilih Nama Annotator:",
    annotator_list
)

st.session_state.annotator = annotator

if annotator == "":
    st.warning("Masukkan nama annotator dulu")
    st.stop()

# =========================
# MAPPING LABEL
# =========================
labeled_map = {
    str(r["id"]): r["label"]
    for r in records
    if r["annotator"] == annotator
}

# =========================
# ANNOTATOR GUIDE
# =========================
with st.sidebar.expander("📘 Annotator Guide"):
    st.markdown("""
### 🎯 Tujuan
Klasifikasi berdasarkan gaya bahasa

### 🧑 Gen Z
- slang, santai, emoji

### 🧑 Milenial
- campuran formal-informal

### 🧑 Gen Alpha
- Slang, emoji

### ⚠️ Catatan
Fokus gaya bahasa, bukan isi
""")

# =========================
# SIDEBAR NAVIGASI
# =========================
st.sidebar.title("📂 Navigasi Data")

st.sidebar.markdown(f"### Progress: {len(labeled_map)}/{len(data)}")

current_id = str(data.iloc[st.session_state.idx]["id"])
st.sidebar.markdown(f"👉 Sedang di ID: {current_id}")
st.sidebar.markdown("""
✔ = sudah dilabel  
○ = belum dilabel
""")
cols_per_row = 5
items_per_page = 100

page = st.sidebar.number_input(
    "Halaman",
    min_value=1,
    max_value=(len(data) // items_per_page) + 1,
    value=1
)

start_idx = (page - 1) * items_per_page
end_idx = min(start_idx + items_per_page, len(data))

for i in range(start_idx, end_idx, cols_per_row):

    cols = st.sidebar.columns(cols_per_row)

    for j in range(cols_per_row):

        if i + j < end_idx:

            idx = i + j

            id_data = str(data.iloc[idx]["id"])

            status = "✔" if id_data in labeled_map else "○"

            if cols[j].button(
                f"{status} {id_data}",
                key=f"nav_{idx}"
            ):
                st.session_state.idx = idx

# =========================
# AMBIL DATA (TIDAK DI-FILTER)
# =========================
row = data.iloc[st.session_state.idx % len(data)]

# =========================
# PROGRESS
# =========================
done = len(labeled_map)
total = len(data)

st.write(f"Progress: {done}/{total}")
st.progress(done / total)

# =========================
# TAMPILKAN TEKS
# =========================
st.subheader("Teks:")
st.write(row["text"])

# =========================
# STATUS LABEL
# =========================
existing = labeled_map.get(str(row["id"]))

if existing:
    st.success(f"Sudah dilabel: {existing}")
else:
    st.warning("Belum dilabel")

# =========================
# RADIO LABEL
# =========================
labels = ["Milenial", "Gen Z", "Gen Alpha"]

default_index = labels.index(existing) if existing in labels else 0

label = st.radio("Pilih label:", labels, index=default_index)

# =========================
# SAVE / UPDATE
# =========================
def save_or_update(id_data, label):

    id_data = str(id_data)

    key = (id_data, annotator)

    if key in record_index_map:

        row_number = record_index_map[key]

        sheet.update_cell(row_number, 3, label)

    else:

        sheet.append_row([id_data, annotator, label])

# =========================
# BUTTON NAVIGASI
# =========================
col1, col2 = st.columns(2)

with col1:
    if st.button("⬅️ Previous"):
        st.session_state.idx -= 1
        st.rerun()

with col2:
    if st.button("Submit & Next ➡️"):

        with st.spinner("Menyimpan label..."):

            save_or_update(str(row["id"]), label)

            st.session_state.idx += 1

            st.cache_data.clear()

        st.rerun()

# =========================
# FEEDBACK MESSAGE (UX HUMAN TOUCH)
# =========================
progress_ratio = done / total

if progress_ratio < 0.3:
    st.info("🙏 Terima kasih atas kesediaan Bapak/Ibu membantu proses anotasi data ini.")
elif progress_ratio < 0.9:
    st.info("✨ Terima kasih atas kontribusinya. Setiap label yang diberikan sangat berarti bagi penelitian ini.")
elif progress_ratio < 1.0:
    st.info("🔥 Sedikit lagi! Terima kasih atas konsistensi Bapak/Ibu dalam proses anotasi ini.")
else:
    st.success("🎉 Terima kasih banyak atas kontribusi Bapak/Ibu dalam proses anotasi data penelitian ini. Seluruh data telah selesai dilabeli 🙏")
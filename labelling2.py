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
def load_data():
    return pd.read_csv(
        "labeling_data.csv",
        encoding="utf-8-sig"
    )
# =========================
# GET RECORDS
# =========================
@st.cache_data(ttl=5)
def get_records():
    return sheet.get_all_records()

records = get_records()

record_index_map = {
    (str(r["id"]), r["annotator"], r.get("phase", "")): i + 2
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

# =========================
# PHASE SELECTION
# =========================
mode = st.selectbox(
    "Pilih Phase Annotation:",
    ["pilot", "final"]
)

# =========================
# LOAD + FILTER DATA
# =========================
data = load_data()

data = data[
    data["phase"] == mode
].reset_index(drop=True)

if annotator == "":
    st.warning("Masukkan nama annotator dulu")
    st.stop()

if st.session_state.idx >= len(data):
    st.session_state.idx = 0

# =========================
# MAPPING LABEL
# =========================
phase_ids = set(data["id"].astype(str))

labeled_map = {
    str(r["id"]): r["label"]
    for r in records
    if (
        r["annotator"] == annotator
        and str(r["id"]) in phase_ids
    )
}

# =========================
# PEDOMAN ANOTASI LENGKAP
# =========================
with st.sidebar.expander("📘 PEDOMAN ANOTASI DATA", expanded=False):

    st.markdown("""
# Klasifikasi Generasi Berdasarkan Gaya Bahasa di Media Sosial Menggunakan IndoBERTweet

---
# 1. Pendahuluan

Pedoman anotasi ini disusun untuk membantu annotator melakukan pelabelan komentar media sosial berdasarkan karakteristik gaya bahasa antar generasi.

Penelitian ini bertujuan membangun model klasifikasi generasi menggunakan pendekatan Natural Language Processing (NLP) dengan model IndoBERTweet.

Fokus utama penelitian adalah mengidentifikasi kecenderungan generasi penulis berdasarkan pola komunikasi dan gaya bahasa yang digunakan dalam teks media sosial.

Karena bahasa media sosial bersifat dinamis, informal, dan sering mengalami overlap antar generasi, proses anotasi dilakukan menggunakan pendekatan:

### “Dominant Linguistic Tendency”

yaitu annotator memilih satu label generasi yang paling dominan berdasarkan karakteristik linguistik dan pragmatik pada komentar.

---

# 2. Tujuan Anotasi

Anotasi dilakukan untuk:

- menghasilkan dataset berkualitas,
- menjaga konsistensi pelabelan,
- mengurangi subjektivitas annotator,
- mendukung proses fine-tuning model IndoBERTweet.

---

# 3. Kategori Label Generasi

Komentar dilabeli ke dalam satu generasi dominan:

| Label | Generasi | Tahun Lahir | Usia Tahun 2023 | Usia Tahun 2025 |
|---|---|---|---|---|
| Gen Y | Millennial | 1981–1996 | 27–42 tahun | 29–44 tahun |
| Gen Z | Generasi Z | 1997–2012 | 11–26 tahun | 13–28 tahun |
| Gen Alpha | Generasi Alpha | 2013 ke atas | 0–10 tahun | 0–12 tahun |

### ⚠️ Catatan penting

Label ditentukan berdasarkan gaya bahasa dan cara komunikasi, bukan usia asli penulis.

Contoh:
- Orang berusia 30 tahun dapat menulis dengan gaya Gen Z.
- Pengguna Gen Z dapat menggunakan gaya komunikasi Millennial.

---

# 4. Prinsip Dasar Anotasi

## 4.1 Fokus pada Gaya Komunikasi

Annotator harus menilai:

- gaya bahasa,
- struktur kalimat,
- pola emosi,
- pilihan kosakata,
- cara berinteraksi,
- framing pemikiran,
- gaya pragmatik komunikasi.

Annotator tidak boleh menentukan label berdasarkan:

❌ foto profil  
❌ username  
❌ gender  
❌ isi opini benar/salah  
❌ asumsi usia pengguna  

---

## 4.2 Gunakan Bukti Linguistik dan Pragmatik

Pelabelan dilakukan berdasarkan pola komunikasi yang muncul dalam teks.

### Contoh benar
“jir relate banget 😭”

Terdapat ciri slang dan ekspresi khas Gen Z.

### Contoh salah
“Kayaknya dia masih SMP.”

Penilaian berdasarkan asumsi usia, bukan isi teks.

---

## 4.3 Satu Komentar = Satu Label Dominan

Setiap komentar wajib diberi satu label:

- Gen Alpha
- Gen Z
- Gen Y

Penelitian ini tidak menggunakan label “Unclear”.

Jika komentar ambigu atau memiliki campuran ciri, annotator tetap harus memilih label berdasarkan kecenderungan komunikasi yang paling dominan.

---

# 5. Prioritas Penilaian

Jika annotator ragu menentukan label, gunakan urutan prioritas berikut:

---

## PRIORITAS 1 — Gaya Pragmatik (Paling Penting)

Tanyakan:

### “Cara komunikasinya paling mirip generasi mana?”

Bukan:

### “Topiknya tentang generasi apa?”

---

## PRIORITAS 2 — Struktur dan Kompleksitas Kalimat

| Struktur | Cenderung |
|---|---|
| Sangat pendek, impulsif | Gen Alpha |
| Conversational dan reflektif | Gen Z |
| Rapi, logis, argumentatif | Gen Y |

---

## PRIORITAS 3 — Pilihan Kosakata dan Slang

| Ciri | Contoh | Cenderung |
|---|---|---|
| Meme/slang hiper-tren | sigma, gyatt, skibidi | Gen Alpha |
| Slang digital + refleksi | relate, coping, vibes | Gen Z |
| Bahasa semi formal/nostalgia | “zaman saya”, “menurut saya” | Gen Y |

---

## PRIORITAS 4 — Pola Emosi

| Pola Emosi | Cenderung |
|---|---|
| Random, absurd, emoji-heavy | Gen Alpha |
| Ekspresif, ironis, hiperbolik | Gen Z |
| Stabil, dijelaskan verbal | Gen Y |

---

## PRIORITAS 5 — Kedewasaan Isi dan Sudut Pandang

| Isi Komentar | Cenderung |
|---|---|
| Reaksi spontan | Gen Alpha |
| Opini personal dan identitas diri | Gen Z |
| Refleksi sosial dan evaluasi nilai | Gen Y |

---

# 6. Karakteristik Tiap Generasi

---

# 6.1 Gen Alpha

## Karakteristik Umum

Komentar sangat dipengaruhi:

- meme culture,
- absurd humor,
- brainrot internet,
- komunikasi ultra-singkat,
- budaya TikTok dan gaming.

Biasanya:
- pendek,
- impulsif,
- minim elaborasi,
- heavily meme-driven.

---

## Ciri Linguistik

### Kosakata Umum

- sigma
- skibidi
- ohio
- gyatt
- rizz
- fanum tax
- cooked
- delulu

---

### Struktur Kalimat

- sangat pendek,
- tidak lengkap,
- acak/asosiatif.

Contoh:
- “sigma ohio 💀”
- “bro cooked 😭”

---

### Gaya Pragmatik

Tujuan utama:
- lucu,
- random,
- absurd,
- bukan diskusi serius.

---

### Indikator Kuat Gen Alpha

✅ Meme tanpa konteks  
✅ Emoji absurd berlebihan  
✅ Humor random lebih dominan daripada isi  
✅ Minim refleksi/opini  

---

# 6.2 Gen Z

## Karakteristik Umum

Gen Z memiliki gaya komunikasi:

- digital-native,
- ekspresif,
- ironis,
- conversational,
- self-aware,
- meme-aware.

Sering:
- mencampur serius dan bercanda,
- menggunakan humor sebagai coping,
- memakai slang internet secara intens.

---

## Ciri Linguistik

### Kosakata Umum

- jir
- anjir
- relate
- vibes
- random
- cringe
- coping
- delulu
- valid
- fomo

---

### Struktur Kalimat

- conversational,
- semi-acak,
- seperti berbicara langsung,
- sering tidak terlalu formal.

Contoh:
- “jujur capek bgt sama sistem kek gini 😭”

---

### Gaya Pragmatik

- kritik personal,
- validasi diri,
- self-deprecating humor,
- opini emosional,
- humor sebagai coping mechanism.

---

### Indikator Kuat Gen Z

✅ Sarkasme dan ironi  
✅ Campuran serius dan bercanda  
✅ Self-aware humor  
✅ Slang digital tinggi  
✅ Oversharing ringan  

---

# 6.3 Gen Y (Millennial)

## Karakteristik Umum

Gaya komunikasi Gen Y cenderung:

- lebih stabil,
- reflektif,
- argumentatif,
- normatif,
- lebih formal dibanding Gen Z.

Fokus komunikasi:
- nilai sosial,
- etika,
- pengalaman,
- pendidikan,
- budaya.

---

## Ciri Linguistik

### Kosakata Umum

- menurut saya
- sebaiknya
- harusnya
- etika
- budaya
- integritas
- sopan santun

---

### Struktur Kalimat

- lebih lengkap,
- logis,
- runtut,
- argumentatif.

Contoh:
- “Menurut saya penggunaan AI tetap harus diverifikasi.”

---

### Gaya Pragmatik

- memberi nasihat,
- menjelaskan konteks,
- membandingkan masa lalu dan sekarang,
- refleksi sosial.

---

### Indikator Kuat Gen Y

✅ Bahasa lebih formal  
✅ Nada reflektif/normatif  
✅ Argumentasi runtut  
✅ Moral framing kuat  

---

# 7. Penanganan Kasus Ambigu

## 7.1 Gen Z vs Gen Alpha

| Jika | Label |
|---|---|
| Masih ada opini/refleksi | Gen Z |
| Hanya meme/random | Gen Alpha |

Contoh:
- “brainrot jir” → Gen Z
- “sigma ohio skibidi 💀” → Gen Alpha

---

## 7.2 Gen Z vs Gen Y

| Jika | Label |
|---|---|
| Santai, sarkastik, emosional | Gen Z |
| Reflektif, normatif, argumentatif | Gen Y |

---

## 7.3 Jangan Fokus pada Satu Kata

Contoh:

“Menurut saya sigma sekarang terlalu overrated.”

Meskipun ada kata “sigma”, pola komunikasi lebih reflektif dan semi formal.

→ Gen Y

---

# 8. Hal yang Tidak Boleh Dijadikan Patokan

Annotator tidak boleh menentukan label berdasarkan:

❌ topik politik  
❌ agama  
❌ profesi  
❌ usia yang disebutkan  
❌ isi opini benar/salah  

Karena semua generasi dapat membahas topik yang sama.

---

# 9. Prosedur Anotasi

## Langkah 1 — Baca Komentar Secara Utuh

Pahami konteks dan pola komunikasi keseluruhan.

---

## Langkah 2 — Identifikasi Ciri Linguistik dan Pragmatik

Perhatikan:
- struktur kalimat,
- slang,
- pola emosi,
- gaya komunikasi,
- kedalaman isi.

---

## Langkah 3 — Tentukan Label Dominan

Pilih:
- Gen Alpha
- Gen Z
- Gen Y

---

# 11. Quality Control (QC)

Sebagian data akan dianotasi oleh lebih dari satu annotator untuk mengukur konsistensi pelabelan.

Jika terjadi perbedaan label:
- gunakan guideline sebagai acuan utama,
- diskusikan alasan anotasi,
- gunakan adjudicator bila diperlukan.

---

# 12. Aturan Final

Jika komentar:
- absurd total → Gen Alpha
- ironis dan digital-native → Gen Z
- reflektif dan normatif → Gen Y

---

# 13. Penutup

Pedoman ini dirancang untuk memastikan proses anotasi:
- konsisten,
- objektif,
- dapat direplikasi,
- sesuai kebutuhan penelitian NLP author profiling pada media sosial.

Karena bahasa media sosial sangat dinamis dan overlap antar generasi, annotator diharapkan fokus pada pola komunikasi dominan, bukan asumsi usia pengguna.
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

st.caption(
    "Dataset berasal dari media sosial periode 2023–2025. "
    "Annotator diharapkan mempertimbangkan konteks tren bahasa digital pada periode tersebut, "
    "namun tetap memprioritaskan gaya komunikasi dominan dalam teks."
)

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

    key = (id_data, annotator, mode)

    if key in record_index_map:

        row_number = record_index_map[key]

        sheet.update_cell(row_number, 3, label)

    else:

        sheet.append_row([
            id_data,
            annotator,
            label,
            mode
        ])

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

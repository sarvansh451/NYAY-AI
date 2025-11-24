# NYAY-AI

# ⚖️ NYAY AI – Legal Assistant & Nearby Help Finder

NYAY AI is a Streamlit-based web app that helps users understand legal problems, scan documents for legal risk, and discover nearby legal services such as lawyers, legal aid centers, police stations, and courts.

> 🚨 **Disclaimer:** NYAY AI is for informational and educational purposes only.  
> It is **not** a substitute for professional legal advice. Always consult a qualified lawyer for real cases.

---

## 🌟 Features

### 1. 🧑‍⚖️ Legal Assistant
- Enter any legal issue in **plain English**.
- Uses a multi-agent workflow (`legal_assistant_crew`) to:
  - Analyze the situation
  - Identify relevant legal sections (e.g., IPC)
  - Suggest precedent-style reasoning
  - Generate a **formal legal-style document/summary**

### 2. 📄 Document Scanner (Legal Risk Analyzer)
Upload a legal document and get **AI-powered risk classification**:

- Supported formats:
  - `PDF`
  - `DOCX`
  - `TXT`
- For each important line/clause:
  - Classifies risk as:
    - 🟢 **SAFE**
    - 🟡 **MODERATE RISK**
    - 🔴 **HIGH RISK**
  - Gives a short explanation in simple language.
- Visual outputs:
  - Summary metrics (total clauses, counts per risk level)
  - Risk distribution bar chart
  - Detailed breakdown grouped by risk level
- Downloadable reports:
  - 📄 **Color-coded PDF report** (generated using ReportLab)
  - 📝 **Plain text report**

### 3. 📍 Find Legal Help Nearby
Find nearby legal resources based on your location:

- Uses **OpenStreetMap / Overpass API** + **geopy**.
- Categories:
  - 👨‍⚖️ Lawyers  
  - 🤝 Legal Aid / NGOs / Social Facilities  
  - 🚔 Police Stations  
  - 🏛️ Courthouses  
- Features:
  - Geocodes your input (city, address, pincode) using **Nominatim**
  - Shows an interactive **Folium map** inside Streamlit
  - Draws a radius circle around your location
  - Lists each place with:
    - Name
    - Address (if available)
    - Phone (if available)
    - Website (if available)
    - Distance (in km)

---

## 🧱 Tech Stack

- **Frontend / UI:** [Streamlit](https://streamlit.io/)
- **AI / LLM:**
  - [Groq](https://groq.com/) client (`groq` Python SDK)
  - Model: `llama-3.3-70b-versatile`
  - Custom multi-agent crew: `legal_assistant_crew` (from `crew.py`)
- **Document Processing:**
  - `PyPDF2` – extract text from PDFs
  - `python-docx` (`docx`) – extract text from DOCX
  - Plain text handling for `.txt`
- **Mapping & Geolocation:**
  - `folium` + `streamlit-folium`
  - `geopy` (`Nominatim` + `geodesic`)
  - Overpass API (OpenStreetMap)
- **Reports:**
  - `reportlab` – generate rich, color-coded PDF reports
- **Environment & Config:**
  - `python-dotenv` – load `.env` variables

---


# ⚖️ Union Shield — Grievance & Disciplinary Tracking Tool

A secure, mobile-friendly web app for UPS union representatives to digitize, extract, validate, and archive grievance and disciplinary forms using AI.

---

## ✨ Features

- **AI-Powered OCR** — Upload a photo of any paper form; Gemini 1.5 Flash extracts all fields automatically
- **Human-in-the-Loop** — Review and correct extracted data before saving
- **Google Sheets Archive** — All records stored in a shared Google Sheet for your team
- **Searchable History** — Filter by employee name, ID, or case type
- **Password Protected** — Simple access control for union rep use only
- **Mobile Responsive** — Works on phones for field use

---

## 🚀 Setup Guide

### Step 1 — Clone & Create Virtual Environment

```bash
git clone <your-repo-url>
cd union-grievance-app

python3 -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### Step 2 — Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

| Variable | Description | Where to get it |
|---|---|---|
| `APP_PASSWORD` | Access code for the app | Set to anything secure |
| `GEMINI_API_KEY` | Google Gemini API key | [aistudio.google.com](https://aistudio.google.com/) (free) |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Path to service account JSON | Google Cloud Console |

### Step 3 — Set Up Google Sheets Access

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable these APIs:
   - **Google Sheets API**
   - **Google Drive API**
4. Go to **IAM & Admin → Service Accounts**
5. Create a service account, then create a JSON key
6. Download the JSON key and save it as `service_account.json` in the project folder
7. Create a Google Sheet named **`Union_Records`** and share it with the service account email (Editor access)

### Step 4 — Get Gemini API Key

1. Visit [aistudio.google.com](https://aistudio.google.com/)
2. Sign in with Google
3. Click **Get API Key** → Create API key
4. Add it to `.env` as `GEMINI_API_KEY`

### Step 5 — Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 📱 Usage Guide

### New Entry Tab
1. Tap **Upload Image** and photograph your paper form
2. Wait ~5 seconds for AI extraction
3. Review all extracted fields — edit anything that's wrong
4. Hit **Save to Google Sheets**

### Search Archive Tab
1. Type an employee name or ID in the search bar
2. Filter by case type if needed
3. Click any row to expand the full incident description

---

## ☁️ Deploying to Streamlit Cloud (Private Instance)

1. Push your code to a **private** GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Under **Advanced Settings → Secrets**, add your `.env` variables in TOML format:

```toml
APP_PASSWORD = "your_secure_password"
GEMINI_API_KEY = "your_gemini_key"
GOOGLE_SERVICE_ACCOUNT_JSON = '{"type": "service_account", ...}'
```

> ⚠️ **Important:** For Streamlit Cloud, use `GOOGLE_SERVICE_ACCOUNT_JSON` (paste full JSON) instead of the file path option.

---

## 🔒 Security Notes

- This app handles UPS employee data — run on a **private** or **local** instance only
- The password in `.env` is basic protection; for higher security consider Streamlit's built-in auth or SSO
- Never commit `service_account.json` or `.env` to version control
- Add these to `.gitignore`:
  ```
  .env
  service_account.json
  venv/
  __pycache__/
  ```

---

## 📁 Project Structure

```
union-grievance-app/
├── app.py              # Main Streamlit UI
├── processor.py        # Gemini AI image extraction
├── database.py         # Google Sheets read/write
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .env                # Your actual secrets (never commit)
└── service_account.json  # Google credentials (never commit)
```

---

## 🛠 Troubleshooting

**"GEMINI_API_KEY not found"** → Check your `.env` file has no quotes around the key value

**"SpreadsheetNotFound"** → Make sure the sheet is named exactly `Union_Records` and shared with service account email

**"Extraction returned empty fields"** → Image quality is too low; try better lighting and hold camera directly overhead

**App won't start** → Run `pip install -r requirements.txt` in your activated virtual environment

---

## 📋 Data Schema (Google Sheets Columns)

| Column | Description |
|---|---|
| `timestamp` | When the record was saved |
| `employee_name` | Full employee name |
| `employee_id` | UPS employee ID |
| `date` | Date of incident |
| `case_type` | Grievance / Discipline / Arbitration / Other |
| `article_violated` | Contract article number |
| `description` | Full incident description |
| `source_file` | Uploaded filename or "manual_entry" |

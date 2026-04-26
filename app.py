import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from dotenv import load_dotenv
import io

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Union Shield · Grievance Tracker",
    page_icon="⚖️",
    layout="centered",                  # ← was "wide", centered works on mobile
    initial_sidebar_state="collapsed",  # ← collapsed by default on mobile
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

:root {
    --gold: #D4A017;
    --gold-light: #F0C040;
    --dark: #0A0A0F;
    --dark-2: #12121A;
    --dark-3: #1C1C28;
    --dark-4: #252535;
    --border: #2E2E45;
    --text: #E8E8F0;
    --text-dim: #8888AA;
    --red: #E53E3E;
    --green: #38A169;
    --blue: #3182CE;
}

* { box-sizing: border-box; }

.stApp {
    background: var(--dark);
    font-family: 'IBM Plex Sans', sans-serif;
    color: var(--text);
}

/* Hide default Streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--dark-2) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--gold) !important;
}

/* Main header */
.app-header {
    background: linear-gradient(135deg, var(--dark-2) 0%, var(--dark-3) 100%);
    border: 1px solid var(--border);
    border-left: 4px solid var(--gold);
    padding: 16px 20px;
    margin-bottom: 20px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 14px;
}
.app-header .shield { font-size: 36px; flex-shrink: 0; }
.app-header h1 {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    color: var(--gold);
    letter-spacing: 3px;
    margin: 0;
    line-height: 1;
}
.app-header p {
    color: var(--text-dim);
    font-size: 0.72rem;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 1px;
    margin: 4px 0 0;
    text-transform: uppercase;
}

/* Tab styling — tighter padding for mobile */
.stTabs [data-baseweb="tab-list"] {
    background: var(--dark-2);
    border-bottom: 1px solid var(--border);
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: var(--text-dim);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 12px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    flex: 1;
    text-align: center;
}
.stTabs [aria-selected="true"] {
    background: transparent !important;
    color: var(--gold) !important;
    border-bottom: 2px solid var(--gold) !important;
}

/* Cards */
.card-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
}

/* Form fields */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: var(--dark-3) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    border-radius: 3px !important;
    font-size: 16px !important; /* Prevents iOS zoom on focus */
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 1px var(--gold) !important;
}
label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    color: var(--text-dim) !important;
}

/* Buttons */
.stButton button {
    font-family: 'IBM Plex Mono', monospace !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    font-size: 0.75rem !important;
    border-radius: 2px !important;
    transition: all 0.15s ease !important;
    min-height: 44px !important; /* Touch-friendly tap target */
}
.stButton button[kind="primary"] {
    background: var(--gold) !important;
    color: var(--dark) !important;
    border: none !important;
    font-weight: 600 !important;
}
.stButton button[kind="secondary"] {
    background: transparent !important;
    color: var(--text-dim) !important;
    border: 1px solid var(--border) !important;
}

/* Upload zone */
.upload-zone {
    background: var(--dark-3);
    border: 2px dashed var(--border);
    border-radius: 4px;
    padding: 32px 20px;
    text-align: center;
}

/* Status messages */
.stAlert {
    border-radius: 3px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
}

/* Divider */
hr { border-color: var(--border) !important; }

/* Mobile responsive */
@media (max-width: 768px) {
    .app-header h1 { font-size: 1.5rem; letter-spacing: 2px; }
    .app-header { padding: 12px 14px; gap: 10px; }
    .app-header .shield { font-size: 28px; }
    .app-header p { font-size: 0.65rem; }
    /* Stack columns on mobile */
    [data-testid="column"] { min-width: 100% !important; }
}
</style>
""", unsafe_allow_html=True)


# ── Authentication ─────────────────────────────────────────────────────────────
def check_password():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 20px 0 10px;">
            <div style="font-size: 2.5rem;">⚖️</div>
            <div style="font-family: 'Bebas Neue', sans-serif; font-size: 1.4rem;
                        color: #D4A017; letter-spacing: 3px;">UNION SHIELD</div>
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem;
                        color: #8888AA; letter-spacing: 2px; margin-top: 4px;">
                GRIEVANCE TRACKER v1.0
            </div>
        </div>
        <hr style="border-color: #2E2E45; margin: 16px 0;">
        """, unsafe_allow_html=True)

        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False

        if not st.session_state.authenticated:
            st.markdown('<p style="font-family: IBM Plex Mono; font-size: 0.7rem; color: #8888AA; letter-spacing: 2px; text-transform: uppercase;">Access Code</p>', unsafe_allow_html=True)
            pwd = st.text_input("Access Code", type="password", placeholder="Enter access code", label_visibility="collapsed")
            if st.button("AUTHENTICATE", type="primary", width='stretch'):
                correct = st.secrets.get("APP_PASSWORD", os.getenv("APP_PASSWORD", "union2024")) if hasattr(st, "secrets") else os.getenv("APP_PASSWORD", "union2024")
                if pwd == correct:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Invalid access code")
            return False
        else:
            st.markdown("""
            <div style="background: rgba(56,161,105,0.1); border: 1px solid rgba(56,161,105,0.3);
                        border-radius: 3px; padding: 10px 14px; margin-bottom: 16px;">
                <span style="font-family: IBM Plex Mono; font-size: 0.7rem; color: #68D391;
                             letter-spacing: 1px;">✓ AUTHENTICATED</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<p style="font-family: IBM Plex Mono; font-size: 0.65rem; color: #8888AA; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;">Quick Stats</p>', unsafe_allow_html=True)

            try:
                from database import get_all_records
                df = get_all_records()
                if df is not None and not df.empty:
                    total = len(df)
                    grievances = len(df[df["case_type"].str.lower() == "grievance"]) if "case_type" in df.columns else 0
                    disciplines = len(df[df["case_type"].str.lower() == "discipline"]) if "case_type" in df.columns else 0
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total", total)
                    with col2:
                        st.metric("Grievances", grievances)
                    st.metric("Disciplines", disciplines)
            except Exception:
                pass

            st.markdown("<hr>", unsafe_allow_html=True)
            if st.button("SIGN OUT", width='stretch'):
                st.session_state.authenticated = False
                st.rerun()
            return True

    return st.session_state.get("authenticated", False)


# ── Main App ───────────────────────────────────────────────────────────────────
if not check_password():
    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center;
                justify-content: center; height: 70vh; text-align: center; padding: 20px;">
        <div style="font-size: 4rem; margin-bottom: 16px;">⚖️</div>
        <div style="font-family: 'Bebas Neue', sans-serif; font-size: 2.5rem;
                    color: #D4A017; letter-spacing: 5px; margin-bottom: 10px;">
            UNION SHIELD
        </div>
        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;
                    color: #8888AA; letter-spacing: 2px; text-transform: uppercase;">
            Grievance &amp; Disciplinary Tracking System
        </div>
        <div style="margin-top: 28px; font-family: 'IBM Plex Mono'; font-size: 0.72rem;
                    background: rgba(212,160,23,0.08);
                    border: 1px solid rgba(212,160,23,0.2); padding: 12px 20px;
                    border-radius: 3px; color: #8888AA;">
            ☰ Open the menu to sign in
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="shield">⚖️</div>
    <div>
        <h1>UNION SHIELD</h1>
        <p>Grievance &amp; Disciplinary Tracker</p>
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📋 NEW ENTRY", "🗂 ARCHIVE"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 · NEW ENTRY
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── Upload section ─────────────────────────────────────────────────────────
    st.markdown('<div class="card-title">UPLOAD FORM IMAGE</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload grievance or disciplinary form",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Form", use_container_width=True)
        st.markdown(f"""
        <div style="font-family: IBM Plex Mono; font-size: 0.68rem; color: #8888AA;
                    margin: 6px 0 12px; padding: 8px 12px;
                    background: rgba(255,255,255,0.03);
                    border: 1px solid #2E2E45; border-radius: 3px;">
            📎 {uploaded_file.name} · {uploaded_file.size / 1024:.1f} KB
        </div>
        """, unsafe_allow_html=True)

        if "extracted" not in st.session_state or st.button("🔄 RE-EXTRACT WITH AI", width='stretch'):
            with st.spinner("⚡ Gemini AI extracting data..."):
                try:
                    from processor import extract_form_data
                    image_bytes = uploaded_file.read()
                    result = extract_form_data(image_bytes, uploaded_file.type)
                    st.session_state.extracted = result
                    st.session_state.upload_name = uploaded_file.name
                    st.success("✓ Extraction complete — review fields below")
                except Exception as e:
                    st.error(f"Extraction error: {e}")
                    st.session_state.extracted = {
                        "employee_name": "", "employee_id": "", "date": "",
                        "case_type": "Grievance", "article_violated": "", "description": ""
                    }
    else:
        st.markdown("""
        <div class="upload-zone">
            <div style="font-size: 2rem; margin-bottom: 10px;">📄</div>
            <div style="font-family: IBM Plex Mono; font-size: 0.75rem; color: #8888AA;
                        letter-spacing: 1px; text-transform: uppercase;">
                Tap to upload form photo<br>
                <span style="font-size: 0.65rem; color: #555570;">JPG or PNG</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Form fields — stacked vertically for mobile ────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="card-title">VALIDATE &amp; EDIT</div>', unsafe_allow_html=True)

    extracted = st.session_state.get("extracted", {})

    emp_name = st.text_input("Employee Name", value=extracted.get("employee_name", ""), placeholder="Full legal name")
    emp_id   = st.text_input("Employee ID",   value=extracted.get("employee_id", ""),   placeholder="UPS-XXXXX")
    inc_date = st.text_input("Date of Incident", value=extracted.get("date", ""),       placeholder="YYYY-MM-DD")

    case_type = st.selectbox(
        "Case Type",
        ["Grievance", "Discipline", "Arbitration", "Other"],
        index=["Grievance", "Discipline", "Arbitration", "Other"].index(extracted.get("case_type", "Grievance"))
        if extracted.get("case_type", "Grievance") in ["Grievance", "Discipline", "Arbitration", "Other"] else 0
    )

    article     = st.text_input("Article Violated", value=extracted.get("article_violated", ""), placeholder="e.g. Article 37")
    description = st.text_area("Description of Incident", value=extracted.get("description", ""), height=150,
                               placeholder="Detail the incident, circumstances, witnesses, and requested remedy...")

    st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

    if st.button("💾  SAVE TO GOOGLE SHEETS", type="primary", width='stretch'):
        if not emp_name or not emp_id or not inc_date:
            st.error("Employee Name, ID, and Date are required.")
        else:
            image_url = ""
            if uploaded_file is not None:
                with st.spinner("📤 Uploading image to Cloudinary..."):
                    try:
                        from database import upload_image_to_cloudinary
                        uploaded_file.seek(0)
                        image_bytes = uploaded_file.read()
                        safe_id    = emp_id.replace("/", "-").replace(" ", "_")
                        safe_date  = inc_date.replace("/", "-").replace(" ", "")
                        ext        = uploaded_file.name.rsplit(".", 1)[-1].lower()
                        cloud_filename = f"{safe_id}_{safe_date}_{uploaded_file.name}"
                        image_url = upload_image_to_cloudinary(
                            image_bytes, cloud_filename,
                            uploaded_file.type or f"image/{ext}",
                        ) or ""
                        if image_url:
                            st.success("✓ Image saved to Cloudinary")
                        else:
                            st.warning("⚠️ Image upload failed — saving without image.")
                    except Exception as e:
                        st.warning(f"⚠️ Cloudinary error: {e}")

            record = {
                "timestamp":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "employee_name":    emp_name,
                "employee_id":      emp_id,
                "date":             inc_date,
                "case_type":        case_type,
                "article_violated": article,
                "description":      description,
                "source_file":      st.session_state.get("upload_name", "manual_entry"),
                "image_url":        image_url,
            }
            try:
                from database import append_record
                success = append_record(record)
                if success:
                    if image_url:
                        st.success(f"✅ Record + image saved! [View form]({image_url})")
                    else:
                        st.success("✅ Record saved to Union_Records!")
                    st.session_state.pop("extracted", None)
                    st.session_state.pop("upload_name", None)
                else:
                    st.error("Failed to save. Check Google Sheets connection.")
            except Exception as e:
                st.error(f"Save error: {e}")

    if st.button("🗑  CLEAR FORM", width='stretch'):
        st.session_state.pop("extracted", None)
        st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    with st.expander("ℹ️  EXTRACTION TIPS"):
        st.markdown("""
        <div style="font-family: IBM Plex Mono; font-size: 0.75rem; color: #8888AA; line-height: 1.8;">
        <b style="color: #D4A017;">BEST RESULTS:</b><br>
        • Good lighting, no shadows across text<br>
        • Hold camera directly above the form<br>
        • All text within frame — crop tightly<br><br>
        <b style="color: #D4A017;">IF INACCURATE:</b><br>
        • Edit any field manually before saving<br>
        • Re-upload a clearer photo and re-extract
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 · SEARCH ARCHIVE
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="card-title">SEARCH ARCHIVE</div>', unsafe_allow_html=True)

    try:
        from database import get_all_records
        df = get_all_records()
        db_connected = df is not None
    except ImportError:
        db_connected = False
        df = None
    except Exception as e:
        db_connected = False
        df = None
        st.error(f"Database connection error: {e}")

    if not db_connected or df is None or df.empty:
        st.info("ℹ️ No records found or Sheets not connected.")
        df = pd.DataFrame(columns=["timestamp","employee_name","employee_id","date","case_type","article_violated","description","source_file","image_url"])

    # Search + filter — stacked on mobile
    search      = st.text_input("Search", placeholder="🔍  Search by employee name or ID...", label_visibility="collapsed")
    type_filter = st.selectbox("Filter by Type", ["All Types", "Grievance", "Discipline", "Arbitration", "Other"], label_visibility="collapsed")

    # Apply filters
    filtered = df.copy()
    if search:
        mask = pd.Series(False, index=filtered.index)
        for col in ["employee_name", "employee_id"]:
            if col in filtered.columns:
                mask |= filtered[col].astype(str).str.lower().str.contains(search.lower(), na=False)
        filtered = filtered[mask]

    if type_filter != "All Types" and "case_type" in filtered.columns:
        filtered = filtered[filtered["case_type"].astype(str).str.lower() == type_filter.lower()]

    # Stats — 2 columns on mobile instead of 4
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Records", len(df))
        g_count = len(df[df["case_type"].astype(str).str.lower() == "grievance"]) if "case_type" in df.columns else 0
        st.metric("Grievances", g_count)
    with col2:
        st.metric("Filtered", len(filtered))
        d_count = len(df[df["case_type"].astype(str).str.lower() == "discipline"]) if "case_type" in df.columns else 0
        st.metric("Disciplines", d_count)

    st.markdown("<hr>", unsafe_allow_html=True)

    if filtered.empty:
        st.markdown("""
        <div style="text-align: center; padding: 40px 20px; color: #8888AA;
                    font-family: IBM Plex Mono; font-size: 0.8rem;">
            NO RECORDS MATCH YOUR SEARCH
        </div>
        """, unsafe_allow_html=True)
    else:
        filtered = filtered.astype(str)

        # Simplified table — fewer columns for mobile readability
        display_cols = [c for c in ["employee_name", "employee_id", "date", "case_type"] if c in filtered.columns]
        if display_cols:
            st.dataframe(
                filtered[display_cols].rename(columns={
                    "employee_name": "Name", "employee_id": "ID",
                    "date": "Date", "case_type": "Type"
                }),
                width='stretch',
                hide_index=True,
            )

        # Detail expanders — single column layout
        st.markdown('<div class="card-title" style="margin-top: 20px;">RECORD DETAILS</div>', unsafe_allow_html=True)
        for idx, row in filtered.iterrows():
            with st.expander(f"📄  {row.get('employee_name','Unknown')} · {row.get('date','')}"):
                st.markdown(f"**Employee:** {row.get('employee_name','N/A')}")
                st.markdown(f"**ID:** `{row.get('employee_id','N/A')}`")
                st.markdown(f"**Date:** {row.get('date','N/A')}")
                st.markdown(f"**Type:** {row.get('case_type','N/A')}")
                st.markdown(f"**Article:** {row.get('article_violated','N/A')}")
                st.markdown(f"**Filed:** {row.get('timestamp','N/A')}")

                image_url = row.get("image_url", "").strip()
                if image_url and image_url != "nan":
                    st.markdown(f"""
                    <a href="{image_url}" target="_blank"
                       style="display: block; margin: 12px 0; padding: 12px 16px;
                              background: rgba(212,160,23,0.1);
                              border: 1px solid rgba(212,160,23,0.35);
                              border-radius: 3px; text-decoration: none;
                              font-family: IBM Plex Mono; font-size: 0.72rem;
                              letter-spacing: 1.5px; color: #D4A017;
                              text-transform: uppercase; text-align: center;">
                        📎 VIEW ORIGINAL FORM IMAGE
                    </a>
                    """, unsafe_allow_html=True)

                st.markdown("**Description:**")
                st.markdown(f"""
                <div style="background: #1C1C28; border-left: 3px solid #D4A017;
                            padding: 12px 14px; border-radius: 3px; font-size: 0.85rem;
                            color: #C8C8D8; line-height: 1.7; margin-top: 6px;">
                    {row.get('description','No description available.')}
                </div>
                """, unsafe_allow_html=True)

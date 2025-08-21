import streamlit as st
import mysql.connector
from config import DB_CONFIG
from modules import welcome, insertcsv, navigator, preview_audit, cleaner_query, analyst, reset, gendata

# Connect to MySQL
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

conn = get_connection()

# Page config
st.set_page_config(page_title="EBI", layout="wide")

# Inject custom styles
st.markdown("""
    <style>
        :root {
            --brand-green: #49A078;
            --brand-green-dark: #3e8865;
            --brand-yellow: #facc15;
            --brand-blue: #2563EB;
            --brand-blue-dark: #1e40af;
            --brand-bg-light: #e8f6ed;
            --brand-bg-gradient-from: #f0fdfa;
            --brand-bg-gradient-to: #d9f99d;
            --brand-footer-bg: #DFF3EA;
            --brand-footer-border: #49A078;
            --brand-footer-text: #333333;
            --brand-white: #ffffff;
            --brand-black: #111111;
        }
        body, .stApp {
            background-color: var(--brand-bg-light) !important;
            color: var(--brand-black) !important;
            font-family: Arial, sans-serif;
        }
        .block-container {
            background: linear-gradient(135deg, var(--brand-bg-gradient-from), var(--brand-bg-gradient-to)) !important;
            color: var(--brand-black) !important;
            border-radius: 8px;
            padding: 2rem;
            max-width: 900px;
            margin: 1rem auto;
        }
        .stSidebar, .sidebar .sidebar-content, .stSidebarContent {
            background-color: var(--brand-green) !important;
            color: var(--brand-black) !important;
        }
        /* Make all sidebar text black */
        .stSidebar .stRadio label, .sidebar .sidebar-content .stRadio label,
        .stSidebar .stMarkdown, .sidebar .sidebar-content .stMarkdown,
        .stSidebar .stText, .sidebar .sidebar-content .stText,
        .stSidebar .stTitle, .sidebar .sidebar-content .stTitle,
        .stSidebar .stHeader, .sidebar .sidebar-content .stHeader {
            color: var(--brand-black) !important;
        }
        .stSidebar .stImage, .sidebar .sidebar-content .stImage {
            /* images remain unchanged */
        }
        .header-container {
            display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;
            background-color: var(--brand-green) !important;
            color: var(--brand-white) !important;
            padding: 1rem;
            border-radius: 8px;
        }
        .header-container img {
            border-radius: 50%; width: 50px; height: 50px;
        }
        .header-title {
            font-size: 1.5rem; font-weight: 600; color: var(--brand-yellow) !important;
        }
        .header-subtitle {
            font-size: 0.9rem; color: var(--brand-white) !important; margin-top: -0.5rem;
        }
        .section-accent {
            background-color: var(--brand-yellow) !important;
            color: var(--brand-black) !important;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 6px;
        }
        /* All Streamlit buttons */
        .stButton button, .stDownloadButton button {
            background-color: var(--brand-green) !important;
            color: var(--brand-black) !important;
            border-radius: 5px !important;
            padding: 0.4rem 1rem !important;
            border: none !important;
            font-weight: bold !important;
            transition: background 0.2s, color 0.2s;
        }
        .stButton button:hover, .stDownloadButton button:hover {
            background-color: var(--brand-green-dark) !important;
            color: var(--brand-yellow) !important;
        }
        /* Export buttons (CSV, JSON, etc.) */
        .stDownloadButton button {
            background-color: var(--brand-yellow) !important;
            color: var(--brand-black) !important;
            border-radius: 5px !important;
            font-weight: bold !important;
            border: 1px solid var(--brand-green) !important;
        }
        .stDownloadButton button:hover {
            background-color: var(--brand-green) !important;
            color: var(--brand-white) !important;
        }
        .streamlit-expanderHeader {
            font-weight: bold;
            color: var(--brand-green) !important;
        }
        /* Input fields, text areas, select boxes */
        input, textarea, select, .stTextInput>div>input, .stTextArea>div>textarea, .stSelectbox>div>div>div {
            background-color: var(--brand-white) !important;
            color: var(--brand-black) !important;
            border-radius: 5px !important;
            border: 1px solid var(--brand-green) !important;
            font-size: 1rem !important;
        }
        .stTextInput input, .stTextArea textarea, .stSelectbox div[role="textbox"], .stSelectbox div[data-baseweb="select"] {
            background-color: var(--brand-white) !important;
            color: var(--brand-black) !important;
            border-radius: 5px !important;
            border: 1px solid var(--brand-green) !important;
        }
        /* Placeholder text color */
        ::placeholder {
            color: var(--brand-green-dark) !important;
            opacity: 1 !important;
        }
        /* Dataframe text color and background */
        .stDataFrame, .stTable {
            color: var(--brand-black) !important;
            background-color: var(--brand-white) !important;
        }
        /* Markdown and labels */
        .markdown-text-container, .stMarkdown, .stLabel, .stRadio label, .stCheckbox label, .stSelectbox label, .stTextInput label, .stTextArea label {
            color: var(--brand-black) !important;
        }
        /* Footer and footer text */
        footer, .footer-text {
            background-color: var(--brand-footer-bg) !important;
            color: var(--brand-footer-text) !important;
            text-align: center;
            padding: 1rem;
            margin-top: 2rem;
            border-top: 2px solid var(--brand-footer-border);
            border-radius: 0 0 8px 8px;
        }
        .footer-text {
            position: fixed;
            bottom: 10px;
            left: 10px;
            font-size: 12px;
            background-color: var(--brand-footer-bg) !important;
            color: var(--brand-footer-text) !important;
            padding: 0.3rem 0.8rem;
            border-radius: 4px;
            border: 1px solid var(--brand-footer-border);
        }
    </style>
""", unsafe_allow_html=True)

# Initialize navigation state
if "page" not in st.session_state:
    st.session_state["page"] = "Welcome"

def navigate_to(target):
    st.session_state["page"] = target

# Sidebar navigation
st.sidebar.image("assets/logo.png", width=60)
st.sidebar.markdown("### 🧠 EBI")
st.sidebar.markdown("_We analyze, you decide_")
selected = st.sidebar.radio("📂 Modules", [
    "Welcome", "Navigator", "Preview & Audit", "Cleaner & Query", "Analyst", "Reset", "Insert CSV", "Generate Data"
], index=["Welcome", "Navigator", "Preview & Audit", "Cleaner & Query", "Analyst", "Reset", "Insert CSV", "Generate Data"].index(st.session_state["page"]))

if selected != st.session_state["page"]:
    navigate_to(selected)

# Header
col1, col2 = st.columns([1, 5])  # adjust ratio as needed

with col1:
    st.image("assets/deric.png", width=60)

with col2:
    st.markdown("""
        <div class="header-title">
            <a href="https://deric-exes-analytics.netlify.app" target="_blank" style="text-decoration:none; color:#2e7d32;">
                EXes Base Inteligence
            </a>
        </div>
        <div class="header-subtitle">Deric — CEO & Founder of EXES</div>
    """, unsafe_allow_html=True)


# Route to selected module
page = st.session_state["page"]
if page == "Welcome": welcome.show()
elif page == "Navigator": navigator.show(conn)
elif page == "Preview & Audit": preview_audit.show(conn)
elif page == "Cleaner & Query": cleaner_query.show(conn)
elif page == "Analyst": analyst.show(conn)
elif page == "Reset": reset.show()
elif page == "Insert CSV": insertcsv.show(conn)
elif page == "Generate Data": gendata.show(conn)

# Footer
st.markdown("<div class='footer-text'>© 2025 EXES Intelligence — We analyze, you decide</div>", unsafe_allow_html=True)
st.markdown("<div class='footer-text'>© 2025 EXES Intelligence — We analyze, you decide</div>", unsafe_allow_html=True)
st.markdown("<div class='footer-text'>© 2025 EXES Intelligence — We analyze, you decide</div>", unsafe_allow_html=True)
st.markdown("<div class='footer-text'>© 2025 EXES Intelligence — We analyze, you decide</div>", unsafe_allow_html=True)

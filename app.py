import streamlit as st
import sqlite3
from config import DB_PATH
from modules import welcome, insertcsv, navigator, preview_audit, cleaner_query, analyst, reset, gendata

# Connect to SQLite
def get_connection():
    return sqlite3.connect(DB_PATH)

conn = get_connection()

# Page configuration
st.set_page_config(page_title="EXES Base Intelligence", layout="wide")

# Inject custom styles
st.markdown("""
    <style>
        :root {
            --brand-green: #49A078; /* Primary green */
            --brand-green-dark: #3e8865; /* Darker green for hover */
            --brand-yellow: #facc15; /* Accent yellow */
            --brand-blue: #2563EB; /* Accent blue */
            --brand-blue-dark: #1e40af; /* Darker blue */
            --brand-bg-light: #e8f6ed; /* Light background */
            --brand-bg-gradient-from: #f0fdfa; /* Gradient start */
            --brand-bg-gradient-to: #d9f99d; /* Gradient end */
            --brand-footer-bg: #49A078; /* Updated to match header */
            --brand-footer-border: #49A078; /* Footer border (unchanged) */
            --brand-white: #ffffff; /* White */
            --brand-black: #111111; /* Black for text */
            --footer-height: 60px; /* Fixed footer height */
        }

        /* Ensure full height layout */
        body, .stApp {
            background-color: var(--brand-bg-light) !important;
            color: var(--brand-black) !important;
            font-family: Arial, Helvetica, sans-serif;
            font-size: 16px;
            line-height: 1.5;
            min-height: 100vh;
            margin: 0;
            display: flex;
            flex-direction: column;
        }

        /* Main content container */
        .block-container {
            background: linear-gradient(135deg, var(--brand-bg-gradient-from), var(--brand-bg-gradient-to)) !important;
            color: var(--brand-black) !important;
            border-radius: 12px;
            padding: 2.5rem;
            max-width: 1000px;
            margin: 1.5rem auto;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            flex-grow: 1;
            padding-bottom: 80px; /* Adjusted for non-fixed footer */
        }

        /* Sidebar: Green background with black text */
        .stSidebar, .sidebar .sidebar-content, .stSidebarContent {
            background-color: var(--brand-green) !important;
            color: var(--brand-black) !important;
            padding: 1.5rem;
            z-index: 1;
        }
        .stSidebar .stRadio label, .stSidebar .stMarkdown, .stSidebar .stText,
        .stSidebar .stTitle, .stSidebar .stHeader {
            color: var(--brand-black) !important;
            font-weight: bold;
        }
        .stSidebar .stRadio label {
            font-size: 1.1rem;
        }

        /* Header: Unchanged */
        .header-container {
            display: flex;
            align-items: center;
            gap: 1.2rem;
            margin-bottom: 1.5rem;
            background-color: var(--brand-green) !important;
            color: var(--brand-black) !important;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .header-container img {
            border-radius: 50%;
            width: 60px;
            height: 60px;
        }
        .header-title {
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--brand-black) !important;
        }
        .header-subtitle {
            font-size: 1rem;
            color: var(--brand-black) !important;
            font-weight: normal;
        }

        /* Section accents */
        .section-accent {
            background-color: var(--brand-yellow) !important;
            color: var(--brand-black) !important;
            padding: 1.5rem;
            margin: 1.5rem 0;
            border-radius: 8px;
        }

        /* Buttons */
        .stButton button, .stDownloadButton button {
            background-color: var(--brand-green) !important;
            color: var(--brand-black) !important;
            border-radius: 8px !important;
            padding: 0.6rem 1.2rem !important;
            border: none !important;
            font-weight: bold !important;
            font-size: 1rem;
            transition: background 0.3s ease, color 0.3s ease;
        }
        .stButton button:hover, .stDownloadButton button:hover {
            background-color: var(--brand-green-dark) !important;
            color: var(--brand-black) !important;
        }
        .stDownloadButton button {
            background-color: var(--brand-yellow) !important;
            color: var(--brand-black) !important;
            border: 1px solid var(--brand-green) !important;
        }
        .stDownloadButton button:hover {
            background-color: var(--brand-green) !important;
            color: var(--brand-black) !important;
        }

        /* Expander headers */
        .streamlit-expanderHeader {
            font-weight: bold;
            color: var(--brand-black) !important;
            font-size: 1.1rem;
        }

        /* Input fields, text areas, select boxes */
        input, textarea, select, .stTextInput>div>input, .stTextArea>div>textarea, 
        .stSelectbox>div>div>div, .stTextInput input, .stTextArea textarea, 
        .stSelectbox div[role="textbox"], .stSelectbox div[data-baseweb="select"] {
            background-color: var(--brand-white) !important;
            color: var(--brand-black) !important;
            border-radius: 8px !important;
            border: 1px solid var(--brand-green) !important;
            font-size: 1rem !important;
            padding: 0.6rem !important;
        }

        /* Dropdown arrows and icons */
        .stSelectbox [data-baseweb="select"] > div::after {
            border-color: var(--brand-black) transparent transparent transparent !important;
        }
        .stSelectbox [data-baseweb="select"] svg, .stSelectbox [data-baseweb="select"] i {
            fill: var(--brand-black) !important;
            color: var(--brand-black) !important;
        }

        /* Placeholder text */
        ::placeholder {
            color: #1e4d36 !important;
            opacity: 1 !important;
            font-weight: normal;
        }

        /* Dataframes and tables */
        .stDataFrame, .stTable {
            color: var(--brand-black) !important;
            background-color: var(--brand-white) !important;
            border-radius: 8px;
        }

        /* Markdown and labels */
        .markdown-text-container, .stMarkdown, .stLabel, .stRadio label, 
        .stCheckbox label, .stSelectbox label, .stTextInput label, .stTextArea label {
            color: var(--brand-black) !important;
            font-weight: bold;
            font-size: 1rem;
        }

        /* Footer: Matches header's colors and positioning */
        footer, .footer-text {
            display: flex;
            align-items: center;
            gap: 1.2rem;
            margin-bottom: 1.5rem;
            background-color: var(--brand-green) !important;
            color: var(--brand-black) !important;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        /* Responsive adjustments */
        @media (max-width: 600px) {
            .block-container {
                padding: 1.5rem;
                padding-bottom: 80px;
            }
            .header-container, footer, .footer-text {
                padding: 1rem;
            }
            .header-title {
                font-size: 1.4rem;
            }
            .header-subtitle {
                font-size: 0.9rem;
            }
            .stSidebar {
                padding: 1rem;
            }
            .stSidebar .stRadio label {
                font-size: 1rem;
            }
        }
        @media (min-width: 601px) and (max-width: 900px) {
            .block-container {
                padding: 2rem;
                padding-bottom: 80px;
            }
            .header-title {
                font-size: 1.6rem;
            }
        }
    </style>
""", unsafe_allow_html=True)

# Initialize navigation state
if "page" not in st.session_state:
    st.session_state["page"] = "Welcome"

# Navigation function
def navigate_to(target):
    st.session_state["page"] = target

# Sidebar navigation
st.sidebar.image("assets/logo.png", width=60)
st.sidebar.markdown("### 🧠 EXES Base Intelligence")
st.sidebar.markdown("_We analyze, you decide_", unsafe_allow_html=True)
selected = st.sidebar.radio("📂 Modules", [
    "Welcome", "Navigator", "Preview & Audit", "Cleaner & Query", "Analyst", 
    "Reset", "Insert CSV", "Generate Data"
], index=["Welcome", "Navigator", "Preview & Audit", "Cleaner & Query", "Analyst", 
          "Reset", "Insert CSV", "Generate Data"].index(st.session_state["page"]))

if selected != st.session_state["page"]:
    st.session_state["page"] = selected

# Ensure a table is selected if required and none is set
def ensure_table_selected(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    if tables and "selected_table" not in st.session_state:
        st.session_state["selected_table"] = tables[0]

page = st.session_state["page"]
if page in ["Preview & Audit", "Cleaner & Query", "Analyst"]:
    ensure_table_selected(conn)

# Header
col1, col2 = st.columns([1, 5])
with col1:
    st.image("assets/deric.png", width=60)
with col2:
    st.markdown("""
        <div class="header-title">
            <a href="https://deric-exes-analytics.netlify.app" target="_blank" style="text-decoration:none; color:#111111;">
                EXES Base Intelligence
            </a>
        </div>
        <div class="header-subtitle">Deric — CEO & Founder of EXES</div>
    """, unsafe_allow_html=True)

# Route to selected module
page = st.session_state["page"]
if page == "Welcome":
    welcome.show()
elif page == "Navigator":
    navigator.show(conn)
elif page == "Preview & Audit":
    preview_audit.show(conn)
elif page == "Cleaner & Query":
    cleaner_query.show(conn)
elif page == "Analyst":
    analyst.show(conn)
elif page == "Reset":
    reset.show()
elif page == "Insert CSV":
    insertcsv.show(conn)
elif page == "Generate Data":
    gendata.show(conn)

# Footer
#st.markdown("<div class='footer-text'>© 2025 EXES Intelligence — We analyze, you decide</div>", unsafe_allow_html=True)
import streamlit as st
import os
from datetime import datetime

LOG_PATH = os.path.join("my_projects", "project_log.txt")

def log_action(action, fname, ftype):
    with open(LOG_PATH, "a") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {action} | {ftype} | {fname}\n")

def show():
    st.subheader("🗂️ My Projects")
    visuals_dir = os.path.join("my_projects", "visuals")
    files_dir = os.path.join("my_projects", "files")

    # --- Unified Project Items Container ---
    st.markdown("""
    <style>
    .project-card {
        background:#f8fafc;
        border-radius:16px;
        width:100%;
        min-height:180px;
        padding:1.2rem;
        margin-bottom:1.5rem;
        box-shadow:0 2px 12px rgba(0,0,0,0.08);
        border:2px solid #49A078;
        overflow-wrap:break-word;
        word-break:break-all;
        display:flex;
        flex-direction:column;
        align-items:center;
    }
    .project-title {
        font-weight:bold;
        font-size:1.1rem;
        color:#2563EB;
        max-width:90%;
        overflow-wrap:break-word;
        word-break:break-all;
        text-align:center;
    }
    .project-meta {
        font-size:0.95rem;
        color:#555;
        text-align:center;
        margin-bottom:0.5rem;
    }
    .project-actions {
        display:flex;
        justify-content:center;
        gap:0.5rem;
        margin-top:0.7rem;
        width:100%;
    }
    .small-btn button {
        padding:2px 8px !important;
        font-size:0.85rem !important;
        border-radius:5px !important;
        min-width:40px !important;
        max-width:80px !important;
    }
    </style>
    <div style="background:#f4f8f6;border-radius:18px;padding:2rem 1rem 1rem 1rem;margin-bottom:2rem;box-shadow:0 4px 16px rgba(0,0,0,0.09);border:2px solid #49A078;">
    """, unsafe_allow_html=True)

    # --- Visuals ---
    st.markdown("### Visuals")
    if os.path.exists(visuals_dir):
        visuals = sorted(os.listdir(visuals_dir), key=lambda x: os.path.getmtime(os.path.join(visuals_dir, x)), reverse=True)
        if visuals:
            cols = st.columns(3)
            for idx, fname in enumerate(visuals):
                fpath = os.path.join(visuals_dir, fname)
                with cols[idx % 3]:
                    with st.container():
                        st.markdown(
                            f"""
                            <div class="project-card">
                                <div style="text-align:center;">
                                    <img src="file://{fpath}" width="180" style="border-radius:10px;margin-bottom:0.7rem;" />
                                </div>
                                <div class="project-title">{fname}</div>
                                <div class="project-meta">Captured: {datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y-%m-%d %H:%M:%S')}</div>
                                <div class="project-actions">
                            """, unsafe_allow_html=True)
                        # Buttons inside card
                        btn_col1, btn_col2 = st.columns([1,1])
                        with btn_col1:
                            if st.button("🗑️", key=f"del_visual_{fname}", help="Delete", use_container_width=False):
                                os.remove(fpath)
                                log_action("DELETE", fname, "visual")
                                st.markdown("<span style='color:#d90429;font-weight:bold;'>Deleted successfully.</span>", unsafe_allow_html=True)
                                st.rerun()
                        with btn_col2:
                            pass  # No rename for visuals
                        st.markdown("</div></div>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='font-weight:bold;color:#d90429;'>No visuals saved yet.</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='font-weight:bold;color:#d90429;'>No visuals saved yet.</span>", unsafe_allow_html=True)

    # --- Files ---
    st.markdown("### Files")
    if os.path.exists(files_dir):
        files = sorted(os.listdir(files_dir), key=lambda x: os.path.getmtime(os.path.join(files_dir, x)), reverse=True)
        if files:
            cols = st.columns(3)
            for idx, fname in enumerate(files):
                fpath = os.path.join(files_dir, fname)
                with cols[idx % 3]:
                    with st.container():
                        st.markdown(
                            f"""
                            <div class="project-card">
                                <div class="project-title">{fname}</div>
                                <div class="project-meta">Saved: {datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y-%m-%d %H:%M:%S')}</div>
                                <div class="project-actions">
                            """, unsafe_allow_html=True)
                        btn_col1, btn_col2 = st.columns([1,1])
                        with btn_col1:
                            st.download_button("⬇️", fpath, file_name=fname, help="Download", use_container_width=False)
                        with btn_col2:
                            if st.button("🗑️", key=f"del_file_{fname}", help="Delete", use_container_width=False):
                                os.remove(fpath)
                                log_action("DELETE", fname, "file")
                                st.markdown("<span style='color:#d90429;font-weight:bold;'>Deleted successfully.</span>", unsafe_allow_html=True)
                                st.rerun()
                        st.markdown("</div></div>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='font-weight:bold;color:#d90429;'>No files saved yet.</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='font-weight:bold;color:#d90429;'>No files saved yet.</span>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # --- Log viewer ---
    st.markdown("### Project Log")
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            logs = f.readlines()
        if logs:
            st.markdown("<div style='background:#f6f6f6;border-radius:8px;padding:1rem;margin-bottom:1rem;'><b>Recent Actions:</b></div>", unsafe_allow_html=True)
            for line in reversed(logs[-20:]):
                st.markdown(f"<div style='font-size:0.95rem;color:#333;padding:0.2rem 0;font-weight:bold;'>{line.strip()}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='font-weight:bold;color:#d90429;'>No actions logged yet.</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='font-weight:bold;color:#d90429;'>No actions logged yet.</span>", unsafe_allow_html=True)

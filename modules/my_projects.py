import streamlit as st
import os
from datetime import datetime

def show():
    st.subheader("🗂️ My Projects")
    visuals_dir = os.path.join("my_projects", "visuals")
    files_dir = os.path.join("my_projects", "files")

    # --- Visuals ---
    st.markdown("### Visuals")
    if os.path.exists(visuals_dir):
        visuals = sorted(os.listdir(visuals_dir), key=lambda x: os.path.getmtime(os.path.join(visuals_dir, x)), reverse=True)
        if visuals:
            cols = st.columns(4)
            for idx, fname in enumerate(visuals):
                fpath = os.path.join(visuals_dir, fname)
                with cols[idx % 4]:
                    st.markdown(
                        f"""
                        <div style="background:#f6f6f6;border-radius:12px;padding:1rem;margin-bottom:1rem;box-shadow:0 2px 8px rgba(0,0,0,0.07);border:1px solid #e0e0e0;">
                            <div style="text-align:center;">
                                <img src="file://{fpath}" width="160" style="border-radius:8px;margin-bottom:0.5rem;" />
                            </div>
                            <div style="font-weight:bold;">{fname}</div>
                            <div style="font-size:0.9rem;color:#555;">Captured: {datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y-%m-%d %H:%M:%S')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    if st.button(f"Delete {fname}", key=f"del_visual_{fname}"):
                        os.remove(fpath)
                        st.rerun()
                    new_name = st.text_input(f"Rename {fname}", value=fname, key=f"rename_visual_{fname}")
                    if st.button(f"Rename {fname}", key=f"rename_btn_visual_{fname}"):
                        os.rename(fpath, os.path.join(visuals_dir, new_name))
                        st.rerun()
        else:
            st.info("No visuals saved yet.")
    else:
        st.info("No visuals saved yet.")

    # --- Files ---
    st.markdown("### Files")
    if os.path.exists(files_dir):
        files = sorted(os.listdir(files_dir), key=lambda x: os.path.getmtime(os.path.join(files_dir, x)), reverse=True)
        if files:
            cols = st.columns(4)
            for idx, fname in enumerate(files):
                fpath = os.path.join(files_dir, fname)
                with cols[idx % 4]:
                    st.markdown(
                        f"""
                        <div style="background:#f6f6f6;border-radius:12px;padding:1rem;margin-bottom:1rem;box-shadow:0 2px 8px rgba(0,0,0,0.07);border:1px solid #e0e0e0;">
                            <div style="font-weight:bold;">{fname}</div>
                            <div style="font-size:0.9rem;color:#555;">Saved: {datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y-%m-%d %H:%M:%S')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.download_button("Download", fpath, file_name=fname)
                    if st.button(f"Delete {fname}", key=f"del_file_{fname}"):
                        os.remove(fpath)
                        st.rerun()
                    new_name = st.text_input(f"Rename {fname}", value=fname, key=f"rename_file_{fname}")
                    if st.button(f"Rename {fname}", key=f"rename_file_btn_{fname}"):
                        os.rename(fpath, os.path.join(files_dir, new_name))
                        st.rerun()
        else:
            st.info("No files saved yet.")
    else:
        st.info("No files saved yet.")

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
            for fname in visuals:
                fpath = os.path.join(visuals_dir, fname)
                st.markdown(
                    f"""
                    <div style="background:#f8fafc;border-radius:16px;padding:1.2rem;margin-bottom:1.5rem;box-shadow:0 2px 12px rgba(0,0,0,0.08);border:2px solid #49A078;">
                        <div style="text-align:center;">
                            <img src="file://{fpath}" width="200" style="border-radius:10px;margin-bottom:0.7rem;" />
                        </div>
                        <div style="font-weight:bold;font-size:1.1rem;color:#2563EB;">{fname}</div>
                        <div style="font-size:0.95rem;color:#555;">Captured: {datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y-%m-%d %H:%M:%S')}</div>
                        <div style="margin-top:0.7rem;">
                            <form>
                                <input type="text" value="{fname}" style="width:70%;padding:0.3rem;border-radius:6px;border:1px solid #49A078;" readonly />
                            </form>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                col1, col2 = st.columns([1,1])
                with col1:
                    if st.button(f"Delete {fname}", key=f"del_visual_{fname}"):
                        os.remove(fpath)
                        st.rerun()
                with col2:
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
            for fname in files:
                fpath = os.path.join(files_dir, fname)
                st.markdown(
                    f"""
                    <div style="background:#f8fafc;border-radius:16px;padding:1.2rem;margin-bottom:1.5rem;box-shadow:0 2px 12px rgba(0,0,0,0.08);border:2px solid #2563EB;">
                        <div style="font-weight:bold;font-size:1.1rem;color:#49A078;">{fname}</div>
                        <div style="font-size:0.95rem;color:#555;">Saved: {datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y-%m-%d %H:%M:%S')}</div>
                        <div style="margin-top:0.7rem;">
                            <form>
                                <input type="text" value="{fname}" style="width:70%;padding:0.3rem;border-radius:6px;border:1px solid #2563EB;" readonly />
                            </form>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                col1, col2, col3 = st.columns([1,1,1])
                with col1:
                    st.download_button("Download", fpath, file_name=fname)
                with col2:
                    if st.button(f"Delete {fname}", key=f"del_file_{fname}"):
                        os.remove(fpath)
                        st.rerun()
                with col3:
                    new_name = st.text_input(f"Rename {fname}", value=fname, key=f"rename_file_{fname}")
                    if st.button(f"Rename {fname}", key=f"rename_file_btn_{fname}"):
                        os.rename(fpath, os.path.join(files_dir, new_name))
                        st.rerun()
        else:
            st.info("No files saved yet.")
    else:
        st.info("No files saved yet.")

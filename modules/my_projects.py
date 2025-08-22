import streamlit as st
import os
from datetime import datetime

def show():
    st.subheader("🗂️ My Projects")
    visuals_dir = os.path.join("my_projects", "visuals")
    files_dir = os.path.join("my_projects", "files")
    st.markdown("### Visuals")
    if os.path.exists(visuals_dir):
        visuals = sorted(os.listdir(visuals_dir), reverse=True)
        for fname in visuals:
            fpath = os.path.join(visuals_dir, fname)
            col1, col2, col3 = st.columns([2,2,1])
            with col1:
                st.image(fpath, width=180)
            with col2:
                st.markdown(f"**{fname}**")
                st.markdown(f"Captured: {datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y-%m-%d %H:%M:%S')}")
            with col3:
                if st.button(f"Delete {fname}", key=f"del_{fname}"):
                    os.remove(fpath)
                    st.experimental_rerun()
                new_name = st.text_input(f"Rename {fname}", value=fname, key=f"rename_{fname}")
                if st.button(f"Rename {fname}", key=f"rename_btn_{fname}"):
                    os.rename(fpath, os.path.join(visuals_dir, new_name))
                    st.experimental_rerun()
    else:
        st.info("No visuals saved yet.")

    st.markdown("### Files")
    if os.path.exists(files_dir):
        files = sorted(os.listdir(files_dir), reverse=True)
        for fname in files:
            fpath = os.path.join(files_dir, fname)
            col1, col2, col3 = st.columns([2,2,1])
            with col1:
                st.markdown(f"**{fname}**")
            with col2:
                st.markdown(f"Saved: {datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y-%m-%d %H:%M:%S')}")
            with col3:
                if st.button(f"Delete {fname}", key=f"del_file_{fname}"):
                    os.remove(fpath)
                    st.experimental_rerun()
                new_name = st.text_input(f"Rename {fname}", value=fname, key=f"rename_file_{fname}")
                if st.button(f"Rename {fname}", key=f"rename_file_btn_{fname}"):
                    os.rename(fpath, os.path.join(files_dir, new_name))
                    st.experimental_rerun()
    else:
        st.info("No files saved yet.")

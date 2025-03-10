import streamlit as st
from pages.ressources.components import Navbar
import pandas as pd

st.set_page_config(page_title="OOPSISE", page_icon="📊", layout="wide")

def main():
    Navbar()
    
    # Cyberpunk-style header
    st.markdown("<h1 style='text-align: center;'>OOPSISE SYSTEM</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #00f2ff;'>Advanced Data Analytics Platform</p>", unsafe_allow_html=True)
    
    # Create a cyberpunk-styled grid layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style='background-color: #1f2430; padding: 20px; border-radius: 5px; border: 1px solid rgba(0, 242, 255, 0.3);'>
            <h3 style='color: #00f2ff;'>SYSTEM STATUS</h3>
            <p>All systems operational</p>
            <div style='background-color: #161b22; padding: 10px; border-radius: 3px;'>
                <code style='color: #00f2ff;'>
                > CONNECTION: ACTIVE<br>
                > SECURITY LEVEL: ALPHA<br>
                > DATA STREAMS: READY<br>
                > ANALYSIS ENGINE: ONLINE
                </code>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background-color: #1f2430; padding: 20px; border-radius: 5px; border: 1px solid rgba(0, 242, 255, 0.3);'>
            <h3 style='color: #00f2ff;'>QUICK ACTIONS</h3>
            <ul style='list-style-type: none; padding-left: 0;'>
                <li style='margin-bottom: 10px; padding: 10px; background-color: #161b22; border-left: 3px solid #00f2ff;'>
                    <a href='pages/dashboard.py' style='text-decoration: none;'>
                        📊 Launch Data Dashboard
                    </a>
                </li>
                <li style='margin-bottom: 10px; padding: 10px; background-color: #161b22; border-left: 3px solid #00f2ff;'>
                    <a href='pages/admin.py' style='text-decoration: none;'>
                        🔒 Access Admin Panel
                    </a>
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background-color: #1f2430; padding: 20px; border-radius: 5px; border: 1px solid rgba(0, 242, 255, 0.3); height: 400px;'>
            <h3 style='color: #00f2ff;'>SYSTEM OVERVIEW</h3>
            <p>Welcome to the OOPSISE Cyberpunk Analytics Platform. This system provides advanced data processing capabilities with a futuristic interface.</p>
            <p>Key Features:</p>
            <ul>
                <li>Real-time data visualization</li>
                <li>CSV & Parquet file processing</li>
                <li>Statistical analysis engine</li>
                <li>Interactive dashboards</li>
            </ul>
            <p>To get started, navigate to the Dashboard and upload your data files.</p>
            <div style='position: absolute; bottom: 20px; right: 20px; font-size: 12px; color: #00f2ff;'>
                v1.0.0 // CYBERPUNK EDITION
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()


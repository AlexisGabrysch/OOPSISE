import streamlit as st
from pages.ressources.components import Navbar , apply_border_glitch_effect, apply_custom_css, footer


st.set_page_config(page_title="OOPSISE", page_icon="📊", layout="wide")

def main():
    apply_custom_css()
    apply_border_glitch_effect()
    Navbar()
    
  # Cyberpunk-style header with enhanced styling
    st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h1 style='font-family: \"Orbitron\", sans-serif; font-size: 2.5rem;'>
            CYBER<span style='color: #ff5900;'>METRICS</span>
        </h1>
        <div style='display: flex; justify-content: center; gap: 10px; margin-top: -10px;'>
            <div style='height: 2px; width: 100px; background: linear-gradient(90deg, rgba(0,242,255,0), #00f2ff, rgba(0,242,255,0));'></div>
            <div style='height: 2px; width: 100px; background: linear-gradient(90deg, rgba(255,89,0,0), #ff5900, rgba(255,89,0,0));'></div>
        </div>
        <p style='color: #00f2ff; font-family: monospace; letter-spacing: 2px; margin-top: 5px;'>
            ADVANCED <span style='color: #ff5900;'>DATA ANALYSIS</span> INTERFACE
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <style>
        /* Glitch overlay effect */
        body::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: repeating-linear-gradient(
                0deg,
                rgba(0, 0, 0, 0.15),
                rgba(0, 0, 0, 0.15) 1px,
                transparent 1px,
                transparent 2px
            );
            pointer-events: none;
            z-index: 9999;
            opacity: 0.3;
        }
        
        /* Random glitch animation */
        @keyframes glitch {
            0% { opacity: 1; }
            7% { opacity: 0.75; }
            10% { opacity: 1; }
            27% { opacity: 1; }
            30% { opacity: 0.75; }
            35% { opacity: 1; }
            52% { opacity: 1; }
            55% { opacity: 0.75; }
            60% { opacity: 1; }
            100% { opacity: 1; }
        }
        
        .stApp::after {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(
                90deg,
                rgba(255, 89, 0, 0.03),
                rgba(0, 242, 255, 0.03)
            );
            pointer-events: none;
            animation: glitch 30s infinite;
            z-index: 9998;
        }
    </style>
    """, unsafe_allow_html=True)
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
        
    
    with col2:
        st.markdown("""
        <div style='background-color: #1f2430; padding: 20px; border-radius: 5px; border: 1px solid rgba(0, 242, 255, 0.3);'>
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
    footer()

if __name__ == "__main__":
    main()


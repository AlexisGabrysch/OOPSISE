import streamlit as st

# Function to display the navigation bar with authentication controls
def Navbar():
    # Cyberpunk-inspired CSS styling
    st.markdown(
        """
        <style>
        /* Global styles */
        .stApp {
            background-color: #141619;
            color: #d8d9da;
        }
        
        /* Header styling */
        h1, h2, h3, h4, h5, h6 {
            color: #00f2ff !important;
            font-family: 'monospace', sans-serif;
            text-shadow: 0 0 10px rgba(0, 242, 255, 0.5);
            border-bottom: 1px solid rgba(0, 242, 255, 0.3);
            padding-bottom: 0.3rem;
        }
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #161b22;
            border-right: 1px solid rgba(0, 242, 255, 0.2);
        }
        
        /* Button styling */
        div.stButton > button {
            width: 100%;
            background-color: #1f2430 !important;
            color: #00f2ff !important;
            border: 1px solid #00f2ff !important;
            padding: 10px;
            font-size: 16px;
            font-family: 'monospace', sans-serif;
            box-shadow: 0 0 5px rgba(0, 242, 255, 0.3);
            transition: all 0.3s ease;
        }
        
        div.stButton > button:hover {
            background-color: #00f2ff !important;
            color: #141619 !important;
            box-shadow: 0 0 15px rgba(0, 242, 255, 0.7);
        }
        
        /* DataFrames and tables */
        .dataframe {
            background-color: #1f2430;
            border: 1px solid rgba(0, 242, 255, 0.3);
            border-radius: 5px;
            font-family: 'monospace', sans-serif;
        }
        
        /* Input widgets */
        .stTextInput > div > div > input, 
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select {
            background-color: #1f2430;
            color: #d8d9da;
            border: 1px solid #00f2ff;
        }
        
        /* File uploader */
        .stFileUploader > div > button {
            background-color: #1f2430 !important;
            color: #00f2ff !important;
            border: 1px solid #00f2ff !important;
        }
        
        /* Success/Error/Warning messages */
        .element-container .stAlert {
            background-color: #1f2430;
            border-left-color: #00f2ff;
        }
        
        /* Container cards with neon border effect */
        .css-1r6slb0, .css-12w0qpk {
            background-color: #1f2430;
            border-radius: 5px;
            border: 1px solid rgba(0, 242, 255, 0.2);
            box-shadow: 0 0 10px rgba(0, 242, 255, 0.1);
            padding: 10px;
        }
        
        /* Navigation link glow effect */
        a {
            color: #00f2ff !important;
            text-decoration: none;
            transition: all 0.2s ease;
        }
        
        a:hover {
            text-shadow: 0 0 8px rgba(0, 242, 255, 0.8);
        }
        
        /* Divider styling */
        hr {
            border-color: rgba(0, 242, 255, 0.3);
        }
        
        /* Grid styling */
        .css-1lcbmhc {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    with st.sidebar:
        st.markdown("## Navigation")
        st.page_link('app.py', label='Accueil', icon='🏠')
        st.page_link('pages/admin.py', label='Admin', icon='🔒')
        st.page_link('pages/dashboard.py', label='Dashboard', icon='📊')
        st.markdown("---")



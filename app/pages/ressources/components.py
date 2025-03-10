import streamlit as st

# Ajoutez cette fonction pour créer un effet de glitch sur les métriques et graphiques

# Custom CSS for Grafana-like cyberpunk styling
def apply_custom_css():
    st.markdown("""
    <style>
        /* Dark background with enhanced grid */
        .main {
            background-color: #0b0f19;
            background-image: 
                linear-gradient(rgba(26, 32, 44, 0.5) 1px, transparent 1px),
                linear-gradient(90deg, rgba(26, 32, 44, 0.5) 1px, transparent 1px);
            background-size: 20px 20px;
            background-position: center;
        }
        
        /* Panel styling with alternating glowing borders */
        .grafana-panel {
            background-color: #181b24;
            border: 1px solid rgba(255, 89, 0, 0.2);
            border-radius: 3px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 0 10px rgba(0, 255, 198, 0.15);
            position: relative;
            overflow: hidden;
        }
        
        .grafana-panel:nth-child(odd) {
            border: 1px solid rgba(0, 255, 198, 0.2);
            box-shadow: 0 0 10px rgba(255, 89, 0, 0.15);
        }
        
        /* Animated border effect for panels */
        .grafana-panel::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, #0b0f19, #ff5900, #00f2ff, #0b0f19);
            background-size: 200% 100%;
            animation: flowingBorder 4s linear infinite;
        }
        
        @keyframes flowingBorder {
            0% { background-position: 0% 0; }
            100% { background-position: 200% 0; }
        }
        
        /* Panel header with neon glow effect */
        .panel-header {
            font-size: 16px;
            font-weight: bold;
            color: #ff5900;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 1px solid rgba(255, 89, 0, 0.3);
            text-shadow: 0 0 5px rgba(255, 89, 0, 0.7);
        }
        
        /* Alternate panel headers with cyan */
        .grafana-panel:nth-child(odd) .panel-header {
            color: #00f2ff;
            border-bottom: 1px solid rgba(0, 242, 255, 0.3);
            text-shadow: 0 0 5px rgba(0, 242, 255, 0.7);
        }
        
        /* Headers with enhanced glow */
        h1, h2, h3 {
            color: #E9F8FD !important;
            font-family: 'Orbitron', sans-serif;
            text-shadow: 0 0 10px rgba(0, 242, 255, 0.7), 0 0 20px rgba(0, 242, 255, 0.4);
            letter-spacing: 1px;
        }
        
        /* Title with multi-color glow */
        h1 {
            background: linear-gradient(90deg, #00f2ff, #ff5900);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 15px rgba(0, 242, 255, 0.6), 0 0 25px rgba(255, 89, 0, 0.6);
        }
        
        /* Text styling with better contrast */
        p, li, .stMarkdown, .stText {
            color: #ced4da !important;
            text-shadow: 0 0 2px rgba(0, 0, 0, 0.8);
        }
        
        /* Button styling with orange hover */
        .stButton>button {
            background-color: #0b0f19;
            color: #00f2ff;
            border: 1px solid #00f2ff;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            background-color: #ff5900;
            color: #0b0f19;
            border: 1px solid #ff5900;
            box-shadow: 0 0 15px rgba(255, 89, 0, 0.8);
        }
        
        /* Alternate button with opposite color scheme */
        .stButton:nth-child(odd)>button {
            color: #ff5900;
            border: 1px solid #ff5900;
        }
        
        .stButton:nth-child(odd)>button:hover {
            background-color: #00f2ff;
            border: 1px solid #00f2ff;
            box-shadow: 0 0 15px rgba(0, 242, 255, 0.8);
        }
        
        /* Widget labels */
        .css-81oif8, .css-17ihxae {
            color: #ff5900 !important;
        }
        
        /* Dataframe styling */
        .dataframe {
            background-color: #181b24 !important;
        }
        
        .dataframe th {
            background-color: #252a37 !important;
            color: #ff5900 !important;
        }
        
        /* Tabs with neon indicator */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #181b24;
            color: #d8d9da;
            border: 1px solid rgba(0, 242, 255, 0.2);
            border-radius: 4px 4px 0px 0px;
            padding: 10px 16px;
            transition: all 0.3s ease;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #181b24 !important;
            color: #ff5900 !important;
            border-bottom: 2px solid #ff5900 !important;
            box-shadow: 0 -2px 8px rgba(255, 89, 0, 0.5);
        }
        
        /* Metric cards with enhanced styling */
        .metric-card {
            background-color: #181b24;
            border-radius: 4px;
            padding: 15px;
            border-left: 3px solid #ff5900;
            box-shadow: 0 0 8px rgba(255, 89, 0, 0.3);
            margin-bottom: 10px;
        }
        
        .metric-card:nth-child(odd) {
            border-left: 3px solid #00f2ff;
            box-shadow: 0 0 8px rgba(0, 242, 255, 0.3);
        }
        
        /* Scrollbars with neon colors */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: #0b0f19;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #252a37;
            border-radius: 5px;
            border: 1px solid #ff5900;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #313846;
            border: 1px solid #00f2ff;
        }
        
        /* Form inputs with neon glow */
        .stTextInput>div>div>input, 
        .stNumberInput>div>div>input,
        .stSelectbox>div>div>select {
            background-color: #1f2430;
            color: #d8d9da;
            border: 1px solid #ff5900 !important;
        }
        
        .stTextInput>div>div>input:focus, 
        .stNumberInput>div>div>input:focus,
        .stSelectbox>div>div>select:focus {
            border: 1px solid #00f2ff !important;
            box-shadow: 0 0 10px rgba(0, 242, 255, 0.5) !important;
        }
        
        /* Progress bar with gradient */
        .stProgress > div > div > div {
            background: linear-gradient(90deg, #00f2ff, #ff5900) !important;
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

def apply_border_glitch_effect():
    st.markdown("""
    <style>
        /* Effet de glitch pour les contours */
        .grafana-panel, .metric-card-container, div.stPlotlyChart, div.element-container div div[data-testid="stMetricValue"] > div {
            position: relative;
            z-index: 1;
            overflow: hidden;
        }
        
        .grafana-panel::after, .metric-card-container::after, div.stPlotlyChart::after, div.element-container div div[data-testid="stMetricValue"] > div::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            border: 1px solid rgba(0, 242, 255, 0.3);
            pointer-events: none;
            z-index: -1;
            animation: glitchBorder 6s infinite;
        }
        
        @keyframes glitchBorder {
            0% {
                clip-path: inset(0 0 0 0);
                border-color: rgba(0, 242, 255, 0.3);
            }
            3% {
                clip-path: inset(0 3px 0 0);
                border-color: rgba(255, 89, 0, 0.5);
            }
            6% {
                clip-path: inset(0 0 3px 0);
                border-color: rgba(0, 242, 255, 0.3);
            }
            9% {
                clip-path: inset(0 0 0 3px);
                border-color: rgba(255, 89, 0, 0.5);
            }
            12% {
                clip-path: inset(3px 0 0 0);
                border-color: rgba(0, 242, 255, 0.3);
            }
            15% {
                clip-path: inset(0 0 0 0);
                border-color: rgba(255, 89, 0, 0.5);
            }
            48% {
                clip-path: inset(0 0 0 0);
                border-color: rgba(0, 242, 255, 0.3);
            }
            50% {
                clip-path: inset(0 3px 0 0);
                border-color: rgba(255, 89, 0, 0.5);
            }
            52% {
                clip-path: inset(0 0 3px 0);
                border-color: rgba(0, 242, 255, 0.3);
            }
            54% {
                clip-path: inset(0 0 0 3px);
                border-color: rgba(255, 89, 0, 0.5);
            }
            56% {
                clip-path: inset(3px 0 0 0);
                border-color: rgba(0, 242, 255, 0.3);
            }
            58% {
                clip-path: inset(0 0 0 0);
                border-color: rgba(255, 89, 0, 0.5);
            }
            82% {
                clip-path: inset(0 0 0 0);
                border-color: rgba(0, 242, 255, 0.3);
            }
            84% {
                clip-path: inset(0 0 3px 0);
                border-color: rgba(255, 89, 0, 0.5);
            }
            86% {
                clip-path: inset(0 3px 0 0);
                border-color: rgba(0, 242, 255, 0.3);
            }
            88% {
                clip-path: inset(0 0 0 0);
                border-color: rgba(255, 89, 0, 0.5);
            }
            100% {
                clip-path: inset(0 0 0 0);
                border-color: rgba(0, 242, 255, 0.3);
            }
        }
        
        /* Harmonisation des couleurs des métriques */
        .metric-card-container {
            background-color: #181b24;
            border-radius: 3px;
            border: 1px solid #00f2ff;
            box-shadow: 0 0 8px rgba(0, 242, 255, 0.3);
            margin-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)
    
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



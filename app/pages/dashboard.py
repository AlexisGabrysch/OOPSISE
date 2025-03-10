import streamlit as st
from pages.ressources.components import Navbar
import pandas as pd
import io
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import geoip2.database
import ipaddress
import os
from urllib.request import urlretrieve
import requests
import zipfile
import shutil
import datetime
from datetime import timedelta

# Directory to store GeoIP database
GEOIP_DIR = os.path.join(os.path.dirname(__file__), '../resources/geoip')

def download_geoip_db():
    """Download and extract the MaxMind GeoLite2 City database if not present"""
    try:
        # Create directory if it doesn't exist
        if not os.path.exists(GEOIP_DIR):
            os.makedirs(GEOIP_DIR)
            
        db_path = os.path.join(GEOIP_DIR, 'GeoLite2-City.mmdb')
        
        # Check if database already exists
        if not os.path.exists(db_path):
            st.info("📡 GeoIP database not found. Downloading (this may take a moment)...")
            
            # For demonstration, using a placeholder URL
            # In production you would use your MaxMind license key
            # This is just a placeholder - you need to provide a valid URL
            license_key = "YOUR_LICENSE_KEY"  # Replace with your MaxMind license key
            url = f"https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={license_key}&suffix=tar.gz"
            
            # You should implement proper download logic
            # This is a simplified placeholder
            st.warning("⚠️ GeoIP database download requires a MaxMind license key. Please obtain a free key from maxmind.com and update the code.")
            
            # Create a placeholder database file so we don't try to download again
            with open(db_path, 'w') as f:
                f.write("placeholder")
                
            return None
        
        return db_path
            
    except Exception as e:
        st.error(f"Error downloading GeoIP database: {str(e)}")
        return None

def get_ip_location(ip, reader):
    """Get location info for an IP address"""
    try:
        # Check if the IP is valid
        ipaddress.ip_address(ip)
        
        # Skip private IPs
        if ipaddress.ip_address(ip).is_private:
            return None
            
        # Look up IP
        if reader:
            response = reader.city(ip)
            return {
                'ip': ip,
                'city': response.city.name,
                'country': response.country.name,
                'latitude': response.location.latitude,
                'longitude': response.location.longitude
            }
    except:
        # Invalid IP or not found
        return None
    
    return None

def extract_ips(df):
    """Extract IP addresses from dataframe and get their locations"""
    ip_src_col = None
    ip_dst_col = None
    
    # Try to find IP source and destination columns
    ip_columns = []
    for col in df.columns:
        col_lower = col.lower()
        if 'ip' in col_lower:
            ip_columns.append(col)
            if 'src' in col_lower or 'source' in col_lower:
                ip_src_col = col
            elif 'dst' in col_lower or 'dest' in col_lower or 'destination' in col_lower:
                ip_dst_col = col
    
    # If no specific src/dst columns found, use the first two IP columns
    if not ip_src_col and len(ip_columns) > 0:
        ip_src_col = ip_columns[0]
    if not ip_dst_col and len(ip_columns) > 1:
        ip_dst_col = ip_columns[1]
        
    if not ip_src_col and not ip_dst_col:
        return None, None, None
        
    # Download GeoIP database
    db_path = download_geoip_db()
    
    if db_path and os.path.exists(db_path) and os.path.getsize(db_path) > 100:
        try:
            # Initialize GeoIP reader
            reader = geoip2.database.Reader(db_path)
            
            # Process IP source addresses
            src_locations = []
            if ip_src_col:
                unique_ips = df[ip_src_col].astype(str).unique()
                for ip in unique_ips:
                    location = get_ip_location(ip, reader)
                    if location:
                        src_locations.append(location)
            
            # Process IP destination addresses
            dst_locations = []
            if ip_dst_col:
                unique_ips = df[ip_dst_col].astype(str).unique()
                for ip in unique_ips:
                    location = get_ip_location(ip, reader)
                    if location:
                        dst_locations.append(location)
            
            # Generate flows between source and destination
            flows = []
            if ip_src_col and ip_dst_col:
                # Group by src-dst pair and count occurrences
                flow_counts = df.groupby([ip_src_col, ip_dst_col]).size().reset_index()
                flow_counts.columns = [ip_src_col, ip_dst_col, 'count']
                
                # Get locations for each flow
                for _, row in flow_counts.iterrows():
                    src_ip = row[ip_src_col]
                    dst_ip = row[ip_dst_col]
                    count = row['count']
                    
                    src_loc = get_ip_location(src_ip, reader)
                    dst_loc = get_ip_location(dst_ip, reader)
                    
                    if src_loc and dst_loc:
                        flows.append({
                            'src_ip': src_ip,
                            'dst_ip': dst_ip,
                            'src_lat': src_loc['latitude'],
                            'src_lon': src_loc['longitude'],
                            'dst_lat': dst_loc['latitude'],
                            'dst_lon': dst_loc['longitude'],
                            'count': count,
                            'src_country': src_loc['country'],
                            'dst_country': dst_loc['country']
                        })
            
            # Close reader
            reader.close()
            
            return src_locations, dst_locations, flows
            
        except Exception as e:
            st.error(f"Error processing IP addresses: {str(e)}")
            return None, None, None
    else:
        st.warning("GeoIP database not available. IP geolocation functionality disabled.")
        return None, None, None

def create_ip_map(src_locations, dst_locations, flows):
    """Create an interactive map showing IP locations and flows"""
    # Create base map
    fig = go.Figure()
    
    # Add source markers
    if src_locations:
        src_df = pd.DataFrame(src_locations)
        fig.add_trace(go.Scattergeo(
            lon=src_df['longitude'],
            lat=src_df['latitude'],
            text=src_df.apply(lambda row: f"Source IP: {row['ip']}<br>Location: {row['city']}, {row['country']}", axis=1),
            mode='markers',
            marker=dict(
                size=8,
                color='rgba(0, 255, 157, 0.8)',
                line=dict(width=1, color='rgba(0, 255, 157, 0.5)'),
                symbol='circle'
            ),
            name='Source IPs',
            hoverinfo='text'
        ))
    
    # Add destination markers
    if dst_locations:
        dst_df = pd.DataFrame(dst_locations)
        fig.add_trace(go.Scattergeo(
            lon=dst_df['longitude'],
            lat=dst_df['latitude'],
            text=dst_df.apply(lambda row: f"Destination IP: {row['ip']}<br>Location: {row['city']}, {row['country']}", axis=1),
            mode='markers',
            marker=dict(
                size=8,
                color='rgba(255, 91, 121, 0.8)',
                line=dict(width=1, color='rgba(255, 91, 121, 0.5)'),
                symbol='circle'
            ),
            name='Destination IPs',
            hoverinfo='text'
        ))
    
    # Add flows
    if flows:
        flows_df = pd.DataFrame(flows)
        
        # Normalize flow counts for line width
        max_count = flows_df['count'].max()
        min_count = flows_df['count'].min()
        flows_df['width'] = 1 + 4 * (flows_df['count'] - min_count) / (max_count - min_count) if max_count > min_count else 2
        
        # Add each flow as a line
        for _, flow in flows_df.iterrows():
            fig.add_trace(go.Scattergeo(
                lon=[flow['src_lon'], flow['dst_lon']],
                lat=[flow['src_lat'], flow['dst_lat']],
                mode='lines',
                line=dict(
                    width=flow['width'],
                    color='rgba(0, 242, 255, 0.6)'
                ),
                text=f"Flow: {flow['src_ip']} → {flow['dst_ip']}<br>Count: {flow['count']}<br>From: {flow['src_country']} To: {flow['dst_country']}",
                hoverinfo='text',
                name=''
            ))
    
    # Update layout
    fig.update_layout(
        template="plotly_dark",
        geo=dict(
            showland=True,
            landcolor='rgb(23, 28, 38)',
            countrycolor='rgba(30, 40, 50, 0.8)',
            coastlinecolor='rgba(0, 242, 255, 0.5)',
            countrywidth=0.5,
            coastlinewidth=0.5,
            showocean=True,
            oceancolor='rgb(11, 15, 25)',
            showlakes=False,
            showrivers=False,
            showframe=False,
            showcountries=True,
            projection_type='natural earth',
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(23, 28, 38, 0.8)',
        plot_bgcolor='rgba(23, 28, 38, 0.8)',
        margin=dict(l=0, r=0, t=10, b=10),
        height=500,
        legend=dict(
            x=0,
            y=0,
            bgcolor='rgba(23, 28, 38, 0.7)',
            bordercolor='rgba(0, 255, 198, 0.2)'
        )
    )
    
    return fig

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# Custom CSS for Grafana-like cyberpunk styling
def apply_custom_css():
    st.markdown("""
    <style>
        /* Dark background with grid */
        .main {
            background-color: #0b0f19;
            background-image: 
                linear-gradient(rgba(26, 32, 44, 0.5) 1px, transparent 1px),
                linear-gradient(90deg, rgba(26, 32, 44, 0.5) 1px, transparent 1px);
            background-size: 20px 20px;
        }
        
        /* Panel styling */
        .css-1r6slb0, .css-1wrcr25 {
            background-color: #181b24 !important;
            border: 1px solid rgba(0, 255, 198, 0.2) !important;
            border-radius: 3px !important;
            padding: 5px 10px !important;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #E9F8FD !important;
            font-family: 'Orbitron', sans-serif;
            text-shadow: 0 0 10px rgba(0, 242, 255, 0.7);
        }
        
        /* Text styling */
        p, li, .stMarkdown, .stText {
            color: #ced4da !important;
        }
        
        /* Button styling */
        .stButton>button {
            background-color: #0b0f19;
            color: #00f2ff;
            border: 1px solid #00f2ff;
        }
        
        .stButton>button:hover {
            background-color: #00f2ff;
            color: #0b0f19;
        }
        
        /* Widget labels */
        .css-81oif8, .css-17ihxae {
            color: #00f2ff !important;
        }
        
        /* Dataframe styling */
        .dataframe {
            background-color: #181b24 !important;
        }
        
        .dataframe th {
            background-color: #252a37 !important;
            color: #00f2ff !important;
        }
        
        /* Custom panels */
        .grafana-panel {
            background-color: #181b24;
            border: 1px solid rgba(0, 255, 198, 0.2);
            border-radius: 3px;
            padding: 15px;
            margin-bottom: 15px;
        }
        
        .panel-header {
            font-size: 16px;
            font-weight: bold;
            color: #E9F8FD;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 1px solid rgba(0, 255, 198, 0.3);
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

def load_data(uploaded_file):
    """Load data from uploaded file based on file extension"""
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    if file_extension == 'csv':
        return pd.read_csv(uploaded_file)
    elif file_extension == 'parquet':
        return pd.read_parquet(uploaded_file)
    else:
        return None
        
def create_metric_card(title, value, delta=None, color="#00f2ff"):
    """Create a Grafana-like metric card"""
    if delta:
        delta_html = f"<span style='color:{'#00ff9d' if float(delta) >= 0 else '#ff5b79'};font-size:0.8rem;'>{'+' if float(delta) >= 0 else ''}{delta}%</span>"
    else:
        delta_html = ""
        
    st.markdown(f"""
    <div style='background-color: #181b24; padding: 15px; border-radius: 3px; border: 1px solid rgba(0, 255, 198, 0.2); margin-bottom: 10px;'>
        <p style='color: rgba(255,255,255,0.7); font-size:0.8rem; margin-bottom:0;'>{title}</p>
        <p style='color: {color}; font-size:1.5rem; font-weight:bold; margin:0;'>{value} {delta_html}</p>
    </div>
    """, unsafe_allow_html=True)

# Function to create a Kibana-like time selector
def time_selector():
    st.markdown("<div class='panel-header'>TIME RANGE</div>", unsafe_allow_html=True)
    
    # Time selector options
    time_options = [
        "Last 15 minutes", 
        "Last 30 minutes", 
        "Last 1 hour", 
        "Last 4 hours",
        "Last 12 hours", 
        "Last 24 hours", 
        "Last 7 days", 
        "Last 30 days", 
        "Last 90 days", 
        "Last year", 
        "Custom range"
    ]
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        time_range = st.selectbox(
            "Select time range",
            time_options,
            index=3,  # Default to "Last 4 hours"
            key="time_range_selector"
        )
    
    with col2:
        refresh_button = st.button("🔄 Refresh", key="refresh_time_button")
    
    # Get current time for reference
    now = datetime.datetime.now()
    
    # Calculate start time based on selection
    if time_range == "Last 15 minutes":
        start_time = now - timedelta(minutes=15)
        time_unit = "minutes"
        time_value = 15
    elif time_range == "Last 30 minutes":
        start_time = now - timedelta(minutes=30)
        time_unit = "minutes"
        time_value = 30
    elif time_range == "Last 1 hour":
        start_time = now - timedelta(hours=1)
        time_unit = "hours"
        time_value = 1
    elif time_range == "Last 4 hours":
        start_time = now - timedelta(hours=4)
        time_unit = "hours"
        time_value = 4
    elif time_range == "Last 12 hours":
        start_time = now - timedelta(hours=12)
        time_unit = "hours"
        time_value = 12
    elif time_range == "Last 24 hours":
        start_time = now - timedelta(hours=24)
        time_unit = "hours" 
        time_value = 24
    elif time_range == "Last 7 days":
        start_time = now - timedelta(days=7)
        time_unit = "days"
        time_value = 7
    elif time_range == "Last 30 days":
        start_time = now - timedelta(days=30)
        time_unit = "days"
        time_value = 30
    elif time_range == "Last 90 days":
        start_time = now - timedelta(days=90)
        time_unit = "days"
        time_value = 90
    elif time_range == "Last year":
        start_time = now - timedelta(days=365)
        time_unit = "days" 
        time_value = 365
    elif time_range == "Custom range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", now - timedelta(days=7))
            start_time_input = st.time_input("Start time", datetime.time(0, 0))
            start_time = datetime.datetime.combine(start_date, start_time_input)
        with col2:
            end_date = st.date_input("End date", now)
            end_time_input = st.time_input("End time", datetime.time(23, 59))
            now = datetime.datetime.combine(end_date, end_time_input)
        time_unit = "custom"
        time_value = None
    
    # Display the absolute time range in Kibana style
    st.markdown(f"""
    <div style='background-color: #181b24; padding: 10px; border-radius: 3px; border: 1px solid rgba(0, 255, 198, 0.2); margin: 10px 0;'>
        <span style='color: rgba(255,255,255,0.7); font-size: 0.8rem;'>Current time range:</span>
        <span style='color: #00f2ff; font-size: 0.9rem; margin-left: 5px;'>{start_time.strftime('%Y-%m-%d %H:%M:%S')} → {now.strftime('%Y-%m-%d %H:%M:%S')}</span>
        <div style='margin-top: 5px;'>
            <span style='color: #00f2ff; font-size: 0.8rem; background-color: rgba(0, 242, 255, 0.1); padding: 3px 8px; border-radius: 10px; border: 1px solid rgba(0, 242, 255, 0.2);'>
                {time_range}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    return start_time, now, time_unit, time_value, refresh_button

def filter_df_by_time(df, timestamp_col, start_time, end_time):
    """Filter dataframe based on timestamp column and time range"""
    if timestamp_col is None:
        st.warning("No timestamp column detected in the dataset. Time filtering is disabled.")
        return df
    
    # Ensure timestamp column is in datetime format using our robust parser
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
        df = parse_timestamp(df, timestamp_col)
    
    # Now filter the dataframe
    try:
        return df[(df[timestamp_col] >= start_time) & (df[timestamp_col] <= end_time)]
    except Exception as e:
        st.error(f"Error filtering by time: {str(e)}")
        return df
# Function to detect timestamp columns in a dataframe
def detect_timestamp_cols(df):
    """Detect potential timestamp columns in a dataframe"""
    timestamp_cols = []
    
    for col in df.columns:
        # Check if column name suggests time
        col_lower = col.lower()
        if any(time_word in col_lower for time_word in ['time', 'date', 'timestamp', 'datetime', 'created', 'modified']):
            timestamp_cols.append(col)
            continue
        
        # Check if column type is datetime
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            timestamp_cols.append(col)
            continue
            
        # Check if column contains datetime strings
        if df[col].dtype == 'object':
            # Sample the column to check for datetime patterns
            sample = df[col].dropna().head(10)
            try:
                pd.to_datetime(sample)
                timestamp_cols.append(col)
            except:
                pass
    
    return timestamp_cols

# Add this function to improve timestamp handling for Elasticsearch/Kibana formats

def parse_timestamp(df, timestamp_col):
    """Parse timestamp column handling multiple formats including Elasticsearch formats"""
    try:
        # First try standard pandas datetime conversion
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        return df
    except Exception:
        pass
    
    try:
        # Try Elasticsearch/Kibana format: "Mar 10, 2025 @ 12:42:28.656"
        pattern = r'([A-Za-z]{3}\s\d{1,2},\s\d{4}\s@\s\d{1,2}:\d{2}:\d{2}\.\d{3})'
        
        # Extract timestamps using regex
        df['temp_timestamp'] = df[timestamp_col].astype(str).str.extract(pattern)[0]
        
        # Apply custom parsing for this format
        df[timestamp_col] = pd.to_datetime(df['temp_timestamp'], format='%b %d, %Y @ %H:%M:%S.%f')
        
        # Drop temporary column
        df = df.drop('temp_timestamp', axis=1)
        return df
    except Exception:
        pass
    
    # Last resort: try common formats one by one
    formats = [
        '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO format with milliseconds
        '%Y-%m-%dT%H:%M:%SZ',     # ISO format without milliseconds
        '%Y-%m-%d %H:%M:%S.%f',   # Standard datetime with milliseconds
        '%Y-%m-%d %H:%M:%S',      # Standard datetime
        '%Y-%m-%d',               # Just date
        '%m/%d/%Y %H:%M:%S',      # US format
        '%d/%m/%Y %H:%M:%S',      # European format
        '%b %d, %Y @ %H:%M:%S.%f' # Elasticsearch format
    ]
    
    for fmt in formats:
        try:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col], format=fmt)
            return df
        except:
            continue
    
    # If all attempts fail, raise a more helpful error
    st.error(f"""
    Could not parse timestamp column '{timestamp_col}'. 
    Example value: '{df[timestamp_col].iloc[0]}' 
    Please check the format or select another column.
    """)
    return df

def main():
    apply_custom_css()
    Navbar()
    
    # Cyberpunk-style header with Grafana look
    st.markdown("<h1 style='text-align: center; font-family: \"Orbitron\", sans-serif;'>CYBER METRICS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #00f2ff; margin-bottom: 30px;'>Advanced Data Analysis Interface</p>", unsafe_allow_html=True)
    
    # Create tabs for different sections (like Grafana)
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Exploration", "⚙️ Settings"])
    
    with tab1:
        # Create columns for layout
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # File upload section with cyberpunk styling
            st.markdown("<div class='grafana-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='panel-header'>DATA SOURCE</div>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "DROP CSV/PARQUET FILE",
                type=["csv", "parquet"],
                help="Supported file formats: CSV and Parquet"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col2:
            if uploaded_file is not None:
                try:
                    # Load and display the data
                    df = load_data(uploaded_file)
                    
                    if df is not None:
                        # Store the dataframe in the session state
                        if "original_df" not in st.session_state:
                            st.session_state.original_df = df
                        
                        # Detect timestamp columns
                        timestamp_cols = detect_timestamp_cols(df)
                        
                        # Create time selector panel if timestamp columns exist
                        if timestamp_cols:
                            st.markdown("<div class='grafana-panel'>", unsafe_allow_html=True)
                            
                            # Add timestamp column selector
                            timestamp_col = st.selectbox(
                                "Select timestamp column",
                                timestamp_cols,
                                key="timestamp_col"
                            )
                            
                            # Add time range selector
                            start_time, end_time, time_unit, time_value, refresh_pressed = time_selector()
                            
                            # Filter the dataframe based on the selected time range
                            filtered_df = filter_df_by_time(df, timestamp_col, start_time, end_time)
                            
                            # Create time histogram to show data distribution
                            if len(filtered_df) > 0:
                                # Convert to datetime if not already
                                if not pd.api.types.is_datetime64_any_dtype(filtered_df[timestamp_col]):
                                    filtered_df[timestamp_col] = pd.to_datetime(filtered_df[timestamp_col])
                                
                                # Create time histogram
                                fig = px.histogram(
                                    filtered_df, 
                                    x=timestamp_col,
                                    nbins=50,
                                    color_discrete_sequence=["#00f2ff"]
                                )
                                
                                fig.update_layout(
                                    template="plotly_dark",
                                    plot_bgcolor='rgba(23, 28, 38, 0.8)',
                                    paper_bgcolor='rgba(23, 28, 38, 0.0)',
                                    margin=dict(l=10, r=10, t=10, b=30),
                                    height=150,
                                    xaxis=dict(
                                        title=None,
                                        showgrid=True,
                                        gridcolor='rgba(26, 32, 44, 0.8)',
                                    ),
                                    yaxis=dict(
                                        title="Count",
                                        showgrid=True,
                                        gridcolor='rgba(26, 32, 44, 0.8)',
                                        title_font=dict(color='#00f2ff', size=10)
                                    ),
                                    bargap=0.05
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Show data metrics for the filtered timeframe
                                data_metrics_cols = st.columns(4)
                                with data_metrics_cols[0]:
                                    create_metric_card("FILTERED ROWS", f"{len(filtered_df):,}")
                                with data_metrics_cols[1]:
                                    percent_kept = round((len(filtered_df) / len(df)) * 100, 1)
                                    create_metric_card("% OF TOTAL", f"{percent_kept}%")
                                with data_metrics_cols[2]:
                                    create_metric_card("START TIME", f"{start_time.strftime('%H:%M:%S')}")
                                with data_metrics_cols[3]:
                                    create_metric_card("END TIME", f"{end_time.strftime('%H:%M:%S')}")
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            # Use filtered_df instead of df for all subsequent operations
                            df = filtered_df
                        
                        # File details panel
                        st.markdown("<div class='grafana-panel'>", unsafe_allow_html=True)
                        st.markdown("<div class='panel-header'>FILE DETAILS</div>", unsafe_allow_html=True)
                        
                        # Display metrics like Grafana
                        metrics_cols = st.columns(4)
                        with metrics_cols[0]:
                            create_metric_card("ROWS", f"{df.shape[0]:,}")
                        with metrics_cols[1]:
                            create_metric_card("COLUMNS", f"{df.shape[1]}")
                        with metrics_cols[2]:
                            nulls_percent = round((df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100, 2) if df.shape[0] * df.shape[1] > 0 else 0
                            create_metric_card("NULL VALUES", f"{nulls_percent}%")
                        with metrics_cols[3]:
                            create_metric_card("MEMORY USAGE", f"{round(df.memory_usage(deep=True).sum() / 1048576, 2)} MB")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Column information panel
                        st.markdown("<div class='grafana-panel'>", unsafe_allow_html=True)
                        st.markdown("<div class='panel-header'>COLUMN INFORMATION</div>", unsafe_allow_html=True)
                        
                        col_info = pd.DataFrame({
                            'Data Type': df.dtypes.astype(str),  # Convert dtype objects to strings
                            'Non-Null Values': df.count(),
                            'Null Values': df.isnull().sum(),
                            'Unique Values': [df[col].nunique() for col in df.columns]
                        })
                        st.dataframe(col_info, use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Sample data panel
                        st.markdown("<div class='grafana-panel'>", unsafe_allow_html=True)
                        st.markdown("<div class='panel-header'>SAMPLE DATA</div>", unsafe_allow_html=True)
                        st.dataframe(df.head(5), use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # IP geolocation panel
                        st.markdown("<div class='grafana-panel'>", unsafe_allow_html=True)
                        st.markdown("<div class='panel-header'>IP GEOLOCATION</div>", unsafe_allow_html=True)
                        
                        # Check if the dataframe might contain IP addresses
                        ip_cols = []
                        for col in df.columns:
                            col_lower = col.lower()
                            if 'ip' in col_lower:
                                ip_cols.append(col)
                        
                        if ip_cols:
                            st.info("🌐 IP address columns detected: " + ", ".join(ip_cols))
                            
                            geoip_process = st.button("🔍 ANALYZE IP LOCATIONS", key="process_ips")
                            
                            if geoip_process:
                                with st.spinner("Extracting IP addresses and looking up locations..."):
                                    src_locations, dst_locations, flows = extract_ips(df)
                                    
                                    if src_locations or dst_locations:
                                        st.success(f"✅ Found {len(src_locations) if src_locations else 0} source IPs and {len(dst_locations) if dst_locations else 0} destination IPs with geolocation data.")
                                        
                                        # Create map
                                        st.subheader("IP Traffic Flow Map")
                                        fig = create_ip_map(src_locations, dst_locations, flows)
                                        st.plotly_chart(fig, use_container_width=True)
                                        
                                        # Show flow statistics
                                        if flows:
                                            st.markdown("<div class='panel-header' style='margin-top:15px;'>TRAFFIC FLOW STATISTICS</div>", unsafe_allow_html=True)
                                            
                                            # Create DataFrame from flows
                                            flow_df = pd.DataFrame(flows)
                                            
                                            # Group by country pairs
                                            country_flows = flow_df.groupby(['src_country', 'dst_country'])['count'].sum().reset_index()
                                            country_flows = country_flows.sort_values('count', ascending=False)
                                            
                                            # Show top country flows
                                            st.markdown("#### Top Country Flows")
                                            st.dataframe(country_flows.head(10), use_container_width=True)
                                            
                                    else:
                                        st.warning("No valid IP addresses with geolocation data found.")
                        else:
                            st.info("No IP address columns detected in this dataset.")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                    else:
                        st.error("Unsupported file format. Please upload a CSV or Parquet file.")
                except Exception as e:
                    st.error(f"Error loading data: {str(e)}")

    with tab2:
        if 'df' in locals():
            st.markdown("<div class='grafana-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='panel-header'>DATA EXPLORER</div>", unsafe_allow_html=True)
            
            # Column selection
            all_cols = df.columns.tolist()
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            datetime_cols = df.select_dtypes(include=['datetime', 'datetime64']).columns.tolist()
            
            # Select mode: Standard viz or Kibana-like discover
            viz_modes = ["Analysis Charts", "Data Discovery"]
            selected_mode = st.radio("Select Mode", viz_modes, horizontal=True, key="viz_mode")
            
            if selected_mode == "Analysis Charts":
                # Chart type selection
                chart_types = ["Distribution Analysis", "Correlation Analysis", "Time Series Analysis", "Categorical Analysis"]
                selected_chart = st.selectbox("Select Analysis Type", chart_types, key="chart_type")
                
                # [All your existing chart code here]
                # This part should remain the same as it already looks great 
                
            elif selected_mode == "Data Discovery":
                # Kibana Discover-like interface
                st.markdown("<div class='panel-header' style='margin-top:15px;'>DISCOVER DATA</div>", unsafe_allow_html=True)
                
                # Search box (filtering)
                search_container = st.container()
                with search_container:
                    search_cols, filter_cols = st.columns([3, 1])
                    with search_cols:
                        search_term = st.text_input("Search in data", key="search_term", 
                                        placeholder="Search...",
                                        help="Enter text to filter across all columns")
                    with filter_cols:
                        search_col = st.selectbox("in column", ["All columns"] + all_cols, key="search_col")
                
                # Filter data based on search
                filtered_df = df.copy()
                if search_term:
                    if search_col == "All columns":
                        mask = pd.DataFrame(False, index=df.index, columns=[0])
                        for col in df.columns:
                            if df[col].dtype == 'object' or df[col].dtype == 'category':
                                mask = mask | df[col].astype(str).str.contains(search_term, case=False, na=False)
                            else:
                                # Convert to string for non-text columns
                                mask = mask | df[col].astype(str).str.contains(search_term, case=False, na=False)
                        filtered_df = df[mask.values]
                    else:
                        filtered_df = df[df[search_col].astype(str).str.contains(search_term, case=False, na=False)]
                
                # Column selector
                st.markdown("<div class='panel-header' style='margin-top:15px;'>AVAILABLE FIELDS</div>", unsafe_allow_html=True)
                
                # Show field counts by type with cyberpunk styling
                col_types = st.columns(4)
                with col_types[0]:
                    create_metric_card("ALL FIELDS", f"{len(all_cols)}")
                with col_types[1]:
                    create_metric_card("NUMERIC", f"{len(numeric_cols)}")
                with col_types[2]:
                    create_metric_card("TEXT", f"{len(categorical_cols)}")
                with col_types[3]:
                    create_metric_card("DATE", f"{len(datetime_cols)}")
                
                # Field selection with expandable sections like Kibana
                col1, col2 = st.columns([1, 3])
                with col1:
                    selected_field_type = st.radio("Field Types", 
                                                ["All", "Numeric", "Text", "Date"],
                                                key="field_type")
                    
                    # Filter columns based on selection
                    if selected_field_type == "All":
                        selectable_cols = all_cols
                    elif selected_field_type == "Numeric":
                        selectable_cols = numeric_cols
                    elif selected_field_type == "Text":
                        selectable_cols = categorical_cols
                    else:  # Date
                        selectable_cols = datetime_cols
                    
                    selected_cols = st.multiselect("Select fields to display", 
                                                selectable_cols,
                                                default=selectable_cols[:5] if len(selectable_cols) > 5 else selectable_cols)
                
                with col2:
                    # Data preview with selected columns only
                    if not selected_cols:
                        selected_cols = all_cols[:5] if len(all_cols) > 5 else all_cols
                    
                    # Show hit count like Kibana
                    st.markdown(f"<div style='color:#00f2ff; margin-bottom:10px;'>Found <span style='font-size:1.2rem; font-weight:bold;'>{len(filtered_df)}</span> hits</div>", 
                                unsafe_allow_html=True)
                    
                    # Pagination controls
                    row_count = len(filtered_df)
                    page_size = st.select_slider("Rows per page", 
                                            options=[10, 20, 50, 100], 
                                            value=20,
                                            key="page_size")
                    
                    max_pages = (row_count // page_size) + (1 if row_count % page_size > 0 else 0)
                    max_pages = max(1, max_pages)  # Ensure at least one page
                    
                    page_number = st.number_input("Page", 
                                            min_value=1, 
                                            max_value=max_pages,
                                            value=1,
                                            key="page_number")
                    
                    start_idx = (page_number - 1) * page_size
                    end_idx = min(start_idx + page_size, row_count)
                    
                    page_data = filtered_df.iloc[start_idx:end_idx]
                    
                    # Display data as interactive table with expandable rows
                    st.dataframe(page_data[selected_cols], use_container_width=True)
                    
                    # Expandable document view (Kibana-like)
                    with st.expander("🔍 Detailed Document View", expanded=False):
                        row_to_view = st.slider("Select Document #", 
                                            min_value=1, 
                                            max_value=len(page_data),
                                            value=1,
                                            key="doc_viewer") - 1
                        
                        if row_to_view < len(page_data):
                            doc = page_data.iloc[row_to_view].to_dict()
                            
                            # Create a Kibana-like document view with JSON format
                            st.markdown("<div class='panel-header' style='margin-top:15px;'>DOCUMENT DETAILS</div>", 
                                    unsafe_allow_html=True)
                            
                            # Build a styled document view
                            doc_html = "<div style='font-family: monospace; background-color: #0f1318; padding: 15px; " + \
                                    "border-radius: 3px; border: 1px solid rgba(0, 255, 198, 0.2);'>"
                            doc_html += "<span style='color: #00f2ff;'>{</span><br>"
                            
                            for key, val in doc.items():
                                doc_html += f"&nbsp;&nbsp;<span style='color: #00ff9d;'>'{key}'</span>: "
                                
                                if isinstance(val, (int, float)):
                                    doc_html += f"<span style='color: #ff5b79;'>{val}</span>,<br>"
                                elif pd.isna(val):
                                    doc_html += "<span style='color: #888888;'>null</span>,<br>"
                                else:
                                    doc_html += f"<span style='color: #E9F8FD;'>'{str(val)}'</span>,<br>"
                            
                            doc_html += "<span style='color: #00f2ff;'>}</span>"
                            doc_html += "</div>"
                            
                            st.markdown(doc_html, unsafe_allow_html=True)
                
                # Data summary using metric cards like Kibana
                st.markdown("<div class='panel-header' style='margin-top:15px;'>DATA INSIGHTS</div>", 
                            unsafe_allow_html=True)
                
                # Display statistics for selected columns
                if selected_cols:
                    # Focus on numeric columns for insights
                    num_insight_cols = [col for col in selected_cols if col in numeric_cols]
                    if num_insight_cols:
                        # Create multiple rows of metrics for better organization
                        for i in range(0, len(num_insight_cols), 4):
                            cols_group = num_insight_cols[i:i+4]
                            metric_cols = st.columns(len(cols_group))
                            
                            for idx, col in enumerate(cols_group):
                                with metric_cols[idx]:
                                    avg_val = filtered_df[col].mean()
                                    create_metric_card(
                                        f"AVG {col.upper()}", 
                                        f"{avg_val:.2f}"
                                    )
                
                # Add visualizations based on selected fields
                if selected_cols:
                    viz_cols = st.columns(2)
                    
                    # For the most meaningful visualizations, we need to detect appropriate columns
                    with viz_cols[0]:
                        st.markdown("<div class='panel-header'>FIELD DISTRIBUTION</div>", 
                                    unsafe_allow_html=True)
                        
                        viz_col = st.selectbox(
                            "Select field to visualize", 
                            selected_cols,
                            key="viz_field"
                        )
                        
                        if viz_col in categorical_cols:
                            # Create bar chart for categorical fields
                            value_counts = filtered_df[viz_col].value_counts().nlargest(10)
                            
                            fig = go.Figure()
                            fig.add_trace(go.Bar(
                                x=value_counts.index,
                                y=value_counts.values,
                                marker_color='rgba(0, 242, 255, 0.7)',
                                marker_line=dict(color='rgba(0, 255, 198, 0.5)', width=1)
                            ))
                        
                            fig.update_layout(
                                template="plotly_dark",
                                plot_bgcolor='rgba(23, 28, 38, 0.8)',
                                paper_bgcolor='rgba(23, 28, 38, 0.8)',
                                margin=dict(l=10, r=10, t=10, b=10),  # tighter margins
                                height=300,
                                xaxis=dict(
                                    title=viz_col,
                                    title_font=dict(color='#00f2ff'),
                                    tickangle=45 if len(value_counts) > 5 else 0
                                ),
                                yaxis=dict(
                                    title="Count",
                                    title_font=dict(color='#00f2ff'),
                                    gridcolor='rgba(26, 32, 44, 0.8)',
                                ),
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                        elif viz_col in numeric_cols:
                            # Create histogram for numeric fields
                            fig = go.Figure()
                            fig.add_trace(go.Histogram(
                                x=filtered_df[viz_col],
                                nbinsx=20,
                                marker_color='rgba(0, 242, 255, 0.7)',
                                marker_line=dict(color='rgba(0, 255, 198, 0.5)', width=1)
                            ))
                            
                            fig.update_layout(
                                template="plotly_dark",
                                plot_bgcolor='rgba(23, 28, 38, 0.8)',
                                paper_bgcolor='rgba(23, 28, 38, 0.8)',
                                margin=dict(l=10, r=10, t=10, b=10),
                                height=300,
                                xaxis=dict(
                                    gridcolor='rgba(26, 32, 44, 0.8)',
                                    title=viz_col,
                                    title_font=dict(color='#00f2ff')
                                ),
                                yaxis=dict(
                                    gridcolor='rgba(26, 32, 44, 0.8)',
                                    title="Count",
                                    title_font=dict(color='#00f2ff')
                                ),
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with viz_cols[1]:
                        st.markdown("<div class='panel-header'>TIME PATTERN</div>", 
                                    unsafe_allow_html=True)
                        
                        # If we have datetime columns, show time-based visualization
                        if datetime_cols:
                            time_col = st.selectbox(
                                "Select time field", 
                                datetime_cols,
                                key="time_field"
                            )
                            
                            # Ensure datetime format
                            if not pd.api.types.is_datetime64_any_dtype(filtered_df[time_col]):
                                try:
                                    filtered_df[time_col] = pd.to_datetime(filtered_df[time_col])
                                except:
                                    st.warning("Could not convert to datetime format")
                            
                            # Create time-based bar chart (documents per time period)
                            time_df = filtered_df.set_index(time_col)
                            time_df = time_df.resample('D').size().reset_index()
                            time_df.columns = [time_col, 'count']
                            
                            fig = go.Figure()
                            fig.add_trace(go.Bar(
                                x=time_df[time_col],
                                y=time_df['count'],
                                marker_color='rgba(0, 242, 255, 0.7)',
                                marker_line=dict(color='rgba(0, 255, 198, 0.5)', width=1)
                            ))
                            
                            fig.update_layout(
                                template="plotly_dark",
                                plot_bgcolor='rgba(23, 28, 38, 0.8)',
                                paper_bgcolor='rgba(23, 28, 38, 0.8)',
                                margin=dict(l=10, r=10, t=10, b=10),
                                height=300,
                                xaxis=dict(
                                    title=time_col,
                                    title_font=dict(color='#00f2ff')
                                ),
                                yaxis=dict(
                                    title="Document Count",
                                    title_font=dict(color='#00f2ff'),
                                    gridcolor='rgba(26, 32, 44, 0.8)',
                                ),
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No time fields available in the dataset")
            
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Please upload a file in the Dashboard tab first")

if __name__ == "__main__":
    main()
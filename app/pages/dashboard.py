import streamlit as st
from pages.ressources.components import Navbar , apply_border_glitch_effect, apply_custom_css
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import ipaddress
from urllib.request import urlretrieve
import requests
import datetime
from datetime import timedelta
import socket                                                                 
                                                                                
def get_ip_location(ip):
    """Get location info for an IP address using ip-api.com"""
    try:
        # Check if the IP is valid
        ipaddress.ip_address(ip)
        
        # Skip private IPs
        if ipaddress.ip_address(ip).is_private:
            return None
            
        # Try to resolve domain names to IP addresses
        try:
            if not ip[0].isdigit():
                ip = socket.gethostbyname(ip)
        except:
            pass
            
        # Look up IP using ip-api.com (no API key needed)
        url = f'http://ip-api.com/json/{ip}'
        response = requests.get(url, timeout=5)
        
        # Check if response is successful
        if response.status_code != 200:
            st.warning(f"API error for IP {ip}: Status code {response.status_code}")
            return None
            
        location_info = response.json()
        
        # Check if response contains error
        if location_info.get('status') == 'fail':
            st.warning(f"API error for IP {ip}: {location_info.get('message', 'Unknown error')}")
            return None
        
        # Return formatted location data
        return {
            'ip': ip,
            'city': location_info.get('city', 'Unknown'),
            'country': location_info.get('country', 'Unknown'),
            'latitude': location_info.get('lat', 0),
            'longitude': location_info.get('lon', 0),
            'region': location_info.get('regionName', 'Unknown'),
            'continent': 'Unknown',  # ip-api doesn't provide continent directly
            'country_code': location_info.get('countryCode', 'Unknown'),
            'continent_code': 'Unknown',  # ip-api doesn't provide continent code directly
            'zip': location_info.get('zip', 'Unknown'),
            'isp': location_info.get('isp', 'Unknown'),
            'org': location_info.get('org', 'Unknown')
        }
    except Exception as e:
        st.warning(f"Error processing IP {ip}: {str(e)}")
        return None
def extract_ips(df):
    """Extract IP addresses from dataframe and get their locations with improved error handling"""
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
        
    
    # Additional logging for debugging
    st.info(f"Using {ip_src_col} as source IP and {ip_dst_col if ip_dst_col else 'no destination column'}")
    
    # Process IP source addresses
    src_locations = []
    if ip_src_col:
        # Limit the number of IPs to process to avoid API rate limiting
        unique_ips = df[ip_src_col].astype(str).dropna().unique()
        unique_ips = [ip for ip in unique_ips[:50] if str(ip).strip() != '' and str(ip).lower() != 'nan']
        
        if len(unique_ips) == 0:
            st.warning(f"No valid source IPs found in column {ip_src_col}")
        else:
            # Create a progress bar
            try:
                progress_text = f"Processing {len(unique_ips)} source IPs..."
                progress_bar = st.progress(0, text=progress_text)
                
                for i, ip in enumerate(unique_ips):
                    try:
                        location = get_ip_location(ip)
                        if location:
                            src_locations.append(location)
                    except Exception as e:
                        st.warning(f"Error processing source IP {ip}: {str(e)}")
                    
                    # Update progress
                    progress_bar.progress((i + 1) / len(unique_ips), 
                                        text=f"Processing source IPs: {i+1}/{len(unique_ips)}")
                    
                # Clear the progress bar when done
                progress_bar.empty()
            except Exception as e:
                st.error(f"Error in progress tracking: {str(e)}")
    
    # Process IP destination addresses or add demo destination
    dst_locations = []
    if ip_dst_col:
        # Limit the number of IPs to process to avoid API rate limiting
        unique_ips = df[ip_dst_col].astype(str).dropna().unique()
        unique_ips = [ip for ip in unique_ips[:50] if str(ip).strip() != '' and str(ip).lower() != 'nan']
        
        if len(unique_ips) == 0:
            st.warning(f"No valid destination IPs found in column {ip_dst_col}")
        else:
            # Create a progress bar
            try:
                progress_text = f"Processing {len(unique_ips)} destination IPs..."
                progress_bar = st.progress(0, text=progress_text)
                
                for i, ip in enumerate(unique_ips):
                    try:
                        location = get_ip_location(ip)
                        if location:
                            dst_locations.append(location)
                    except Exception as e:
                        st.warning(f"Error processing destination IP {ip}: {str(e)}")
                    
                    # Update progress
                    progress_bar.progress((i + 1) / len(unique_ips), 
                                        text=f"Processing destination IPs: {i+1}/{len(unique_ips)}")
                    
                # Clear the progress bar when done
                progress_bar.empty()
            except Exception as e:
                st.error(f"Error in progress tracking: {str(e)}")
    
    # SOLUTION: Generate demo destination location for Lyon, France if we don't have destinations
    if not dst_locations or len(dst_locations) == 0:
        st.info("Adding demo destination location in Lyon, France for visualization")
        # Add a destination in Lyon, France
        demo_destination = {
            'ip': '169.254.1.1',  # Placeholder IP
            'city': 'Lyon',
            'country': 'France',
            'latitude': 45.7589,
            'longitude': 4.8414,
            'region': 'Rhône-Alpes',
            'continent': 'Europe',
            'country_code': 'FR',
            'continent_code': 'EU',
            'zip': '69000',
            'isp': 'Demo ISP',
            'org': 'Demo Organization'
        }
        dst_locations = [demo_destination]
    
    # Generate flows between source and destination
    flows = []
    if src_locations and dst_locations:
        try:
            # Determine if we should use actual flows from data or just create demo flows
            if ip_src_col and ip_dst_col:
                # Créer des dictionnaires pour recherche rapide
                src_ip_map = {loc['ip']: loc for loc in src_locations}
                dst_ip_map = {loc['ip']: loc for loc in dst_locations}
                
                # Group by src-dst pair and count occurrences
                try:
                    flow_counts = df.groupby([ip_src_col, ip_dst_col]).size().reset_index()
                    flow_counts.columns = [ip_src_col, ip_dst_col, 'count']
                    
                    # Limiter à 100 flux maximum pour de meilleures performances
                    if len(flow_counts) > 100:
                        flow_counts = flow_counts.nlargest(100, 'count')
                    
                    # Get locations for each flow
                    for _, row in flow_counts.iterrows():
                        src_ip = str(row[ip_src_col])
                        dst_ip = str(row[ip_dst_col])
                        
                        if src_ip.lower() == 'nan' or dst_ip.lower() == 'nan':
                            continue
                        
                        if src_ip in src_ip_map and dst_ip in dst_ip_map:
                            src_loc = src_ip_map[src_ip]
                            dst_loc = dst_ip_map[dst_ip]
                            
                            # S'assurer que toutes les données sont valides
                            if (src_loc.get('latitude') is not None and 
                                src_loc.get('longitude') is not None and 
                                dst_loc.get('latitude') is not None and 
                                dst_loc.get('longitude') is not None):
                                
                                flow = {
                                    'src_ip': src_ip,
                                    'dst_ip': dst_ip,
                                    'src_lat': float(src_loc['latitude']),
                                    'src_lon': float(src_loc['longitude']),
                                    'dst_lat': float(dst_loc['latitude']),
                                    'dst_lon': float(dst_loc['longitude']),
                                    'count': int(row['count']),
                                    'src_country': src_loc.get('country', 'Unknown'),
                                    'dst_country': dst_loc.get('country', 'Unknown'),
                                    'src_city': src_loc.get('city', 'Unknown'),
                                    'dst_city': dst_loc.get('city', 'Unknown'),
                                    'src_isp': src_loc.get('isp', 'Unknown'),
                                    'dst_isp': dst_loc.get('isp', 'Unknown'),
                                    'src_org': src_loc.get('org', 'Unknown'),
                                    'dst_org': dst_loc.get('org', 'Unknown'),
                                }
                                flows.append(flow)
                except Exception as e:
                    st.warning(f"Could not generate flows from data: {str(e)}")
            
            # Si nous n'avons pas assez de flux, créer des flux de démonstration
            # entre toutes nos sources et notre destination Lyon
            if len(flows) == 0 and len(src_locations) > 0:
                st.info("Creating demonstration flows to Lyon, France")
                
                # Get our Lyon destination
                lyon_dest = dst_locations[0]
                
                # Create a demo flow from each source to Lyon
                for src_loc in src_locations:
                    flow = {
                        'src_ip': src_loc['ip'],
                        'dst_ip': lyon_dest['ip'],
                        'src_lat': float(src_loc['latitude']),
                        'src_lon': float(src_loc['longitude']),
                        'dst_lat': float(lyon_dest['latitude']),
                        'dst_lon': float(lyon_dest['longitude']),
                        'count': 1,  # Example count
                        'src_country': src_loc.get('country', 'Unknown'),
                        'dst_country': lyon_dest.get('country', 'France'),
                        'src_city': src_loc.get('city', 'Unknown'),
                        'dst_city': lyon_dest.get('city', 'Lyon'),
                        'src_isp': src_loc.get('isp', 'Unknown'),
                        'dst_isp': lyon_dest.get('isp', 'Demo ISP'),
                        'src_org': src_loc.get('org', 'Unknown'),
                        'dst_org': lyon_dest.get('org', 'Demo Organization'),
                    }
                    flows.append(flow)
            
            # Additional logging
            st.success(f"Generated {len(flows)} attack flow paths")
            
        except Exception as e:
            st.error(f"Error generating flows: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
    else:
        st.warning("Need both source and destination locations to create flow lines")
    
    return src_locations, dst_locations, flows
def create_ip_map(src_locations, dst_locations, flows):
    """Create an interactive map showing IP locations and flows with optimized performance"""
    
    # Create base map with cyberpunk styling but less demanding effects
    fig = go.Figure()
    
    # Add source markers with simplified styling
    if src_locations:
        src_df = pd.DataFrame(src_locations)
        fig.add_trace(go.Scattergeo(
            lon=src_df['longitude'],
            lat=src_df['latitude'],
            text=src_df.apply(lambda row: (
                f"Source IP: {row['ip']}<br>" +
                f"Location: {row['city']}, {row['region']}, {row['country']}<br>" +
                f"ISP: {row.get('isp', 'Unknown')}<br>" +
                f"Organization: {row.get('org', 'Unknown')}<br>" +
                f"Coordinates: {row['latitude']:.4f}, {row['longitude']:.4f}"
            ), axis=1),
            mode='markers',
            marker=dict(
                size=10,
                color='rgba(0, 255, 157, 1.0)',
                line=dict(width=1, color='rgba(0, 255, 157, 0.5)'),
                symbol='circle',
                opacity=0.9,
            ),
            name='Source IPs',
            hoverinfo='text'
        ))
    
    # Add destination markers with simplified styling
    if dst_locations:
        dst_df = pd.DataFrame(dst_locations)
        fig.add_trace(go.Scattergeo(
            lon=dst_df['longitude'],
            lat=dst_df['latitude'],
            text=dst_df.apply(lambda row: (
                f"Destination IP: {row['ip']}<br>" +
                f"Location: {row['city']}, {row['region']}, {row['country']}<br>" +
                f"ISP: {row.get('isp', 'Unknown')}<br>" +
                f"Organization: {row.get('org', 'Unknown')}<br>" +
                f"Coordinates: {row['latitude']:.4f}, {row['longitude']:.4f}"
            ), axis=1),
            mode='markers',
            marker=dict(
                size=10,
                color='rgba(255, 91, 121, 1.0)',
                line=dict(width=1, color='rgba(255, 91, 121, 0.5)'),
                symbol='diamond',
                opacity=0.9,
            ),
            name='Destination IPs',
            hoverinfo='text'
        ))
    
    # Draw optimized flow lines without curves or glowing effects
    # IMPORTANT FIX: Use a different approach for drawing lines to prevent ricochets
    if flows:
        # Limit number of flows to improve performance
        max_flows = min(50, len(flows))
        flows_to_display = flows[:max_flows]
        
        # For each flow, draw a direct line (not curved)
        for flow in flows_to_display:
            # Get source and destination coordinates
            src_lon = flow['src_lon']
            src_lat = flow['src_lat']
            dst_lon = flow['dst_lon']
            dst_lat = flow['dst_lat']
            
            # CRITICAL FIX: Prevent ricocheting by handling the 180° meridian crossing
            lon_diff = abs(src_lon - dst_lon)
            
            # If the difference is greater than 180°, we're probably crossing the meridian
            if lon_diff > 180:
                # Skip this flow as it would cause a ricochet effect
                continue
            
            # Add a simplified line trace (direct path without curves)
            fig.add_trace(go.Scattergeo(
                lon=[src_lon, dst_lon],
                lat=[src_lat, dst_lat],
                mode='lines',
                line=dict(
                    width=1.5,  # Reduce line width for better performance
                    color='rgba(0, 242, 255, 0.8)',
                ),
                opacity=0.8,
                text=(
                    f"Flow: {flow.get('src_ip', 'Unknown')} → {flow.get('dst_ip', 'Unknown')}<br>" +
                    f"Count: {flow.get('count', 'N/A')}<br>" +
                    f"From: {flow.get('src_city', 'Unknown')}, {flow.get('src_country', 'Unknown')}<br>" +
                    f"To: {flow.get('dst_city', 'Unknown')}, {flow.get('dst_country', 'Unknown')}"
                ),
                hoverinfo='text',
                showlegend=False
            ))
    
    # Update layout with simplified styling
    fig.update_layout(
        template="plotly_dark",
        geo=dict(
            showland=True,
            landcolor='rgb(10, 15, 25)',
            countrycolor='rgba(30, 50, 70, 1.0)',
            coastlinecolor='rgba(0, 242, 255, 0.5)',
            countrywidth=0.5,
            coastlinewidth=0.5,
            showocean=True,
            oceancolor='rgb(5, 10, 20)',
            showlakes=False,
            showrivers=False,
            showframe=False,
            showcountries=True,
            # IMPORTANT: Use orthographic projection to avoid distortion at high latitudes
            projection_type='orthographic',  # Changed from natural earth for better line paths
            projection=dict(
                rotation=dict(lon=-10, lat=25, roll=0)  # Center view for better visibility
            ),
            bgcolor='rgba(0,0,0,0)',
            resolution=50,
        ),
        paper_bgcolor='rgba(10, 15, 25, 0.95)',
        plot_bgcolor='rgba(10, 15, 25, 0.95)',
        margin=dict(l=0, r=0, t=10, b=10),
        height=550,  # Slightly reduced height for better performance
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(10, 15, 25, 0.7)',
            bordercolor=None,  # Remove border
            font=dict(size=10, color="#00f2ff")
        ),
        # Add simple buttons to change projection for better exploration
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                buttons=[
                    dict(
                        args=[{"geo.projection.type": "orthographic", 
                               "geo.projection.rotation": {"lon": -10, "lat": 25, "roll": 0}}],
                        label="Globe",
                        method="relayout"
                    ),
                    dict(
                        args=[{"geo.projection.type": "natural earth", 
                               "geo.center": {"lon": 0, "lat": 0}}],
                        label="Flat",
                        method="relayout"
                    ),
                    dict(
                        args=[{"geo.projection.type": "mercator", 
                               "geo.center": {"lon": 0, "lat": 0}}],
                        label="Mercator",
                        method="relayout"
                    )
                ],
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.1,
                y=1.1,
                xanchor="right",
                yanchor="top",
                bgcolor="rgba(10, 15, 25, 0.7)",
            )
        ]
    )
    
    # IMPORTANT: Remove the border shapes that cause rendering issues
    # Instead, add a simple title with cyberpunk styling
    fig.update_layout(
        title=dict(
            text="CYBERPUNK ATTACK FLOW MAP",
            font=dict(
                family="Orbitron, monospace",
                size=16,
                color="#00f2ff"
            ),
            x=0.5,
            y=0.02,
            xanchor='center',
            yanchor='bottom'
        )
    )
    
    return fig
st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

@st.cache_data(ttl=3600) # Cache data for one hour
def cached_load_data(uploaded_file):
    """Load data from uploaded file based on file extension with header detection"""
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    if file_extension == 'csv':
        # Lire les premières lignes pour vérifier si elles contiennent un header
        try:
            # Lire quelques lignes pour l'analyse
            sample = pd.read_csv(uploaded_file, nrows=5)
            uploaded_file.seek(0)  # Réinitialiser le pointeur du fichier
            
            # Vérifier si les en-têtes sont présents en comparant avec les en-têtes attendus
            expected_headers = ["timestamp", "name", "rule", "interface_in", "interface_out", "mac", 
                              "src_ip", "dst_ip", "len", "tos", "prec", "ttl", "id", "df", "proto", 
                              "src_port", "dst_port", "seq", "ack", "window", "flags", "flags2", 
                              "urgp", "uid", "gid", "mark"]
            
            # Si les colonnes actuelles sont des nombres (0, 1, 2, ...) ou ne correspondent pas aux en-têtes attendus
            if all(str(col).isdigit() for col in sample.columns) or not any(col in expected_headers for col in sample.columns):
                st.info("En-têtes CSV non détectés. Utilisation des en-têtes prédéfinis.")
                return pd.read_csv(uploaded_file, header=None, names=expected_headers)
            else:
                return pd.read_csv(uploaded_file)
                
        except Exception as e:
            st.error(f"Erreur lors de la vérification des en-têtes: {str(e)}")
            # Essayons une approche de secours avec les en-têtes prédéfinis
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, header=None, names=expected_headers)
            
    elif file_extension == 'parquet':
        # Les fichiers Parquet ont généralement un schéma avec des noms de colonnes
        return pd.read_parquet(uploaded_file)
        
    elif file_extension in ['xls', 'xlsx']:
        # Pour les fichiers Excel
        return pd.read_excel(uploaded_file)
        
    else:
        st.error(f"Format de fichier non pris en charge: .{file_extension}")
        return None
        
def create_metric_card(title, value, delta=None):
    """Create a Grafana-like metric card with cyberpunk colors, harmonized with cyan"""
    # Use consistent cyan color for all metrics
    color = "#00f2ff"
        
    if delta:
        delta_color = "#00ff9d" if float(delta) >= 0 else "#ff5900"
        delta_html = f"<span style='color:{delta_color};font-size:0.8rem;'>{'+' if float(delta) >= 0 else ''}{delta}%</span>"
    else:
        delta_html = ""
    
    glow_color = "rgba(0, 242, 255, 0.3)"
        
    st.markdown(f"""
    <div class='metric-card-container' style='background-color: #181b24; padding: 15px; border-radius: 3px; 
         border: 1px solid {color}; box-shadow: 0 0 8px {glow_color}; margin-bottom: 10px;'>
        <p style='color: rgba(255,255,255,0.7); font-size:0.8rem; margin-bottom:0;'>{title}</p>
        <p style='color: {color}; font-size:1.5rem; font-weight:bold; margin:0;'>{value} {delta_html}</p>
    </div>
    """, unsafe_allow_html=True)
    
def create_stacked_area_chart(df, timestamp_col, group_col):
    """Create a cyberpunk-styled stacked area chart for temporal visualization"""
    if timestamp_col not in df.columns or group_col not in df.columns:
        st.error(f"Columns {timestamp_col} or {group_col} not found in dataframe")
        return None
    
    # Make sure timestamp is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
        try:
            df = parse_timestamp(df.copy(), timestamp_col)
        except Exception as e:
            st.error(f"Could not parse timestamp column: {str(e)}")
            return None
    
    # Group data by timestamp and group column
    # We need to count occurrences for each group per time period
    
    # First, determine the appropriate time resolution based on data range
    min_date = df[timestamp_col].min()
    max_date = df[timestamp_col].max()
    date_range = (max_date - min_date).total_seconds()
    
    if date_range < 3600:  # Less than 1 hour
        freq = '1min'
        date_format = '%H:%M:%S'
    elif date_range < 86400:  # Less than 1 day
        freq = '1H'
        date_format = '%H:%M'
    elif date_range < 604800:  # Less than 1 week
        freq = '1D'
        date_format = '%Y-%m-%d'
    elif date_range < 2592000:  # Less than 1 month
        freq = '1W'
        date_format = '%Y-%m-%d'
    else:
        freq = '1M'
        date_format = '%Y-%m'
    
    # Create a copy of the dataframe with just timestamp and group columns
    chart_df = df[[timestamp_col, group_col]].copy()
    
    # Ensure group column is string type
    chart_df[group_col] = chart_df[group_col].astype(str)
    
    # For categorical columns with too many unique values, limit to top N
    if chart_df[group_col].nunique() > 10:
        top_groups = chart_df[group_col].value_counts().nlargest(10).index.tolist()
        chart_df.loc[~chart_df[group_col].isin(top_groups), group_col] = 'Other'
    
    # Get counts for each group by time period
    chart_df['count'] = 1
    
    # Resample to desired frequency 
    # Set timestamp as index
    chart_df = chart_df.set_index(timestamp_col)
    
    # Group by time period and group column
    temp = chart_df.groupby([pd.Grouper(freq=freq), group_col])['count'].sum().reset_index()
    
    # Reshape for area chart
    pivot_df = temp.pivot(index=timestamp_col, columns=group_col, values='count').fillna(0)
    
    # Create stacked area chart with cyberpunk styling
    fig = go.Figure()
    
    # Define cyberpunk colors palette
    colors = [
        '#00f2ff',  # cyan
        '#ff5900',  # orange
        '#00ff9d',  # green
        '#a742f5',  # purple
        '#ff3864',  # pink
        '#ffb000',  # yellow
        '#36a2eb',  # blue
        '#29c7ac',  # teal
        '#ff6384',  # red
        '#00b8d9',  # light blue
        '#ff9e00',  # amber
    ]
    
    # Add traces for each group
    for i, col in enumerate(pivot_df.columns):
        color = colors[i % len(colors)]
        color_rgba = f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.7)"
        
        fig.add_trace(go.Scatter(
            x=pivot_df.index,
            y=pivot_df[col],
            mode='lines',
            stackgroup='one',
            name=col,
            line=dict(width=0.5, color=color),
            fillcolor=color_rgba,
            hovertemplate='%{y} events<br>%{x}<extra>' + col + '</extra>'
        ))
    
    # Apply cyberpunk styling
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='rgba(23, 28, 38, 0.8)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=10, r=10, t=30, b=10),
        height=350,
        legend=dict(
            orientation="h",
            y=1.02,
            x=0.5,
            xanchor="center",
            font=dict(color='#d8d9da', size=10),
            bgcolor='rgba(23, 28, 38, 0.7)',
            bordercolor='rgba(0, 242, 255, 0.2)'
        ),
        xaxis=dict(
            title=None,
            showgrid=True,
            gridcolor='rgba(26, 32, 44, 0.8)',
            showline=True,
            linecolor='rgba(0, 242, 255, 0.5)',
            tickformat=date_format,
            tickfont=dict(color='#d8d9da')
        ),
        yaxis=dict(
            title='Event Count',
            showgrid=True,
            gridcolor='rgba(26, 32, 44, 0.8)',
            showline=True,
            linecolor='rgba(0, 242, 255, 0.5)',
            tickfont=dict(color='#d8d9da'),
            title_font=dict(color='#00f2ff')
        ),
        hovermode='x unified'
    )
    
    # Add a subtle glow effect around the plot area
    fig.update_layout(
        shapes=[
            # Bottom border with gradient
            dict(
                type="rect",
                xref="paper", yref="paper",
                x0=0, y0=0, x1=1, y1=0.02,
                line_width=0,
                fillcolor="rgba(0, 242, 255, 0.3)",
                layer="below"
            ),
            # Top border with gradient
            dict(
                type="rect",
                xref="paper", yref="paper",
                x0=0, y0=0.98, x1=1, y1=1,
                line_width=0,
                fillcolor="rgba(0, 242, 255, 0.3)",
                layer="below"
            )
        ]
    )
    
    return fig
def cyberpunk_plot_layout(fig, title=None, height=400):
    """Apply cyberpunk styling to plotly figures with orange accents"""
    # Define colors
    bg_color = '#181b24'
    grid_color = 'rgba(40, 45, 60, 0.8)'
    text_color = '#d8d9da'
    accent_colors = ['#00f2ff', '#ff5900', '#00ff9d', '#a742f5']

    # Update layout
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor=bg_color,
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        height=height,
        title=dict(
            text=title,
            font=dict(
                size=18,
                color='#ff5900',
                family='Orbitron'
            ),
            x=0.5
        ) if title else None,
        font=dict(
            family='monospace',
            color=text_color
        ),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor=grid_color,
            zerolinecolor='rgba(255, 89, 0, 0.3)',
            tickfont=dict(color=text_color)
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1, 
            gridcolor=grid_color,
            zerolinecolor='rgba(0, 242, 255, 0.3)',
            tickfont=dict(color=text_color)
        ),
        legend=dict(
            font=dict(color=text_color),
            bgcolor='rgba(24, 27, 36, 0.7)',
            bordercolor='rgba(255, 89, 0, 0.2)',
        )
    )

    # Add a grid effect in the background
    fig.add_shape(
        type="rect",
        xref="paper", yref="paper",
        x0=0, y0=0, x1=1, y1=1,
        line=dict(color="rgba(0,0,0,0)"),
        layer="below",
        fillcolor="rgba(0,0,0,0)",
        opacity=0.1
    )

    # Add a subtle glow effect around the plot
    fig.update_layout(
        shapes=[
            # Bottom border with gradient
            dict(
                type="rect",
                xref="paper", yref="paper",
                x0=0, y0=0, x1=1, y1=0.02,
                line_width=0,
                fillcolor="rgba(255, 89, 0, 0.3)",
                layer="below"
            ),
            # Top border with gradient
            dict(
                type="rect",
                xref="paper", yref="paper",
                x0=0, y0=0.98, x1=1, y1=1,
                line_width=0,
                fillcolor="rgba(0, 242, 255, 0.3)",
                layer="below"
            )
        ]
    )

    # Update the colors of any traces if they exist
    if fig.data:
        for i, trace in enumerate(fig.data):
            color_idx = i % len(accent_colors)
            try:
                if isinstance(trace, go.Bar) or isinstance(trace, go.Histogram):
                    trace.marker.color = accent_colors[color_idx]
                    trace.marker.line = dict(width=0.5, color=accent_colors[(color_idx+1) % len(accent_colors)])
                elif isinstance(trace, go.Scatter):
                    trace.line.color = accent_colors[color_idx]
                elif hasattr(trace, 'marker') and trace.marker:
                    trace.marker.color = accent_colors[color_idx]
            except:
                pass

    return fig
# Function to create a Kibana-like time selector
def time_selector(on_refresh_callback=None):
    """
    Kibana-style time selector with refresh button
    Returns time range parameters and a boolean indicating if refresh was clicked
    """
    st.markdown("<div class='panel-header'>TIME RANGE</div>", unsafe_allow_html=True)
    
    # Initialize session state for time range parameters if they don't exist
    if "time_range_option" not in st.session_state:
        st.session_state.time_range_option = "Last 4 hours"
    if "custom_start_date" not in st.session_state:
        st.session_state.custom_start_date = datetime.datetime.now() - timedelta(days=7)
    if "custom_start_time" not in st.session_state:
        st.session_state.custom_start_time = datetime.time(0, 0)
    if "custom_end_date" not in st.session_state:
        st.session_state.custom_end_date = datetime.datetime.now()
    if "custom_end_time" not in st.session_state:
        st.session_state.custom_end_time = datetime.time(23, 59)
    if "last_refresh_time" not in st.session_state:
        st.session_state.last_refresh_time = datetime.datetime.now()
    
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
    
    # Track if options were changed since last refresh
    options_changed = False
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # When the time range selection changes, we'll just update the session state
        # but not trigger a refresh
        time_range = st.selectbox(
            "Select time range",
            time_options,
            index=time_options.index(st.session_state.time_range_option),
            key="time_range_selector",
            on_change=lambda: setattr(st.session_state, 'time_range_option', st.session_state.time_range_selector)
        )
        
        # Track if user changed the selection
        if time_range != st.session_state.time_range_option:
            options_changed = True
            st.session_state.time_range_option = time_range
    
    # Handle refresh button with a callback
    with col2:
        def on_refresh():
            st.session_state.last_refresh_time = datetime.datetime.now()
            if on_refresh_callback:
                on_refresh_callback()
        
        refresh_button = st.button("🔄 Refresh", key="refresh_time_button", on_click=on_refresh)
    
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
            start_date = st.date_input("Start date", 
                                      st.session_state.custom_start_date, 
                                      key="start_date")
            start_time_input = st.time_input("Start time", 
                                           st.session_state.custom_start_time, 
                                           key="start_time")
            
            # Check if values changed
            if start_date != st.session_state.custom_start_date:
                st.session_state.custom_start_date = start_date
                options_changed = True
            if start_time_input != st.session_state.custom_start_time:
                st.session_state.custom_start_time = start_time_input
                options_changed = True
                
            start_time = datetime.datetime.combine(start_date, start_time_input)
        with col2:
            end_date = st.date_input("End date", 
                                    st.session_state.custom_end_date,
                                    key="end_date")
            end_time_input = st.time_input("End time", 
                                         st.session_state.custom_end_time,
                                         key="end_time")
            
            # Check if values changed
            if end_date != st.session_state.custom_end_date:
                st.session_state.custom_end_date = end_date
                options_changed = True
            if end_time_input != st.session_state.custom_end_time:
                st.session_state.custom_end_time = end_time_input
                options_changed = True
                
            now = datetime.datetime.combine(end_date, end_time_input)
        time_unit = "custom"
        time_value = None
    
    # Display the absolute time range in Kibana style with last refresh time
    last_refresh = st.session_state.last_refresh_time.strftime('%Y-%m-%d %H:%M:%S')
    
    st.markdown(f"""
    <div style='background-color: #181b24; padding: 10px; border-radius: 3px; border: 1px solid rgba(0, 255, 198, 0.2); margin: 10px 0;'>
        <span style='color: rgba(255,255,255,0.7); font-size: 0.8rem;'>Current time range:</span>
        <span style='color: #00f2ff; font-size: 0.9rem; margin-left: 5px;'>{start_time.strftime('%Y-%m-%d %H:%M:%S')} → {now.strftime('%Y-%m-%d %H:%M:%S')}</span>
        <div style='margin-top: 5px; display: flex; justify-content: space-between;'>
            <span style='color: #00f2ff; font-size: 0.8rem; background-color: rgba(0, 242, 255, 0.1); padding: 3px 8px; border-radius: 10px; border: 1px solid rgba(0, 242, 255, 0.2);'>
                {time_range}
            </span>
            <span style='color: rgba(255,255,255,0.5); font-size: 0.8rem;'>
                Last refreshed: {last_refresh}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # If options changed but refresh wasn't clicked, show an indicator
    if options_changed and not refresh_button:
        st.markdown("""
        <div style='background-color: #181b24; padding: 8px; border-radius: 3px; border: 1px solid rgba(255, 91, 121, 0.3); margin: 10px 0; display: flex; align-items: center;'>
            <span style='color: #ff5b79; font-size: 0.9rem;'>⚠️ Time range changed but not applied. Click Refresh to update data.</span>
        </div>
        """, unsafe_allow_html=True)
    
    return start_time, now, time_unit, time_value, refresh_button
def filter_df_by_time(df, timestamp_col, start_time, end_time):
    """Filter dataframe based on timestamp column and time range with improved parsing"""
    if timestamp_col is None or timestamp_col not in df.columns:
        st.warning("No valid timestamp column selected. Time filtering is disabled.")
        return df
    
    try:
        # Use our improved parser to handle the timestamp column
        parsed_df = parse_timestamp(df.copy(), timestamp_col)
        
        # Check if parsing was successful
        if not pd.api.types.is_datetime64_any_dtype(parsed_df[timestamp_col]):
            st.warning(f"Could not convert '{timestamp_col}' to a valid datetime format. Using original data.")
            return df
        
        # Apply the time filter
        filtered_df = parsed_df[(parsed_df[timestamp_col] >= start_time) & 
                               (parsed_df[timestamp_col] <= end_time)]
        
        # Log information about how many rows were filtered
        original_rows = len(df)
        filtered_rows = len(filtered_df)
        st.info(f"Time filter applied: {filtered_rows} of {original_rows} rows ({filtered_rows/original_rows*100:.1f}%) match the selected time range.")
        
        return filtered_df
        
    except Exception as e:
        st.error(f"Error during time filtering: {str(e)}")
        # Fallback to unfiltered data
        return df
# Function to detect timestamp columns in a dataframe
def detect_timestamp_cols(df):
    """Detect potential timestamp columns with enhanced pattern recognition"""
    timestamp_cols = []
    
    for col in df.columns:
        # Check if column name suggests time
        col_lower = col.lower()
        if any(time_word in col_lower for time_word in 
               ['time', 'date', 'timestamp', '@timestamp', 'datetime', 'created', 'modified', 
                'log_time', 'event_time', 'start', 'end', 'occurred']):
            timestamp_cols.append(col)
            continue
        
        # Check if column type is already datetime
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            timestamp_cols.append(col)
            continue
            
        # Sample the column to check for datetime patterns (use more samples)
        if df[col].dtype == 'object':
            sample = df[col].dropna().head(20).astype(str)
            
            # Enhanced pattern detection for timestamps
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}',                      # ISO date
                r'\d{1,2}/\d{1,2}/\d{2,4}',                # US/EU date
                r'[A-Za-z]{3}\s\d{1,2},\s\d{4}',           # Month name date
                r'\d{1,2}:\d{2}:\d{2}',                    # Time
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}',          # ISO datetime
                r'@',                                       # Elasticsearch @ symbol
                r'\d{2}-[A-Za-z]{3}-\d{4}',                # DD-MMM-YYYY
                r'\d{14}',                                  # YYYYMMDDHHMMSS
                r'\d{1,2}\s+[A-Za-z]{3}\s+\d{4}'           # Day Month Year
            ]
            
            if any(sample.str.contains(pattern, regex=True).any() for pattern in date_patterns):
                timestamp_cols.append(col)
                continue
    
    # If we found too many potential timestamp columns, filter to the most likely ones
    if len(timestamp_cols) > 5:
        # Try to determine the most likely timestamp columns
        likely_cols = []
        for col in timestamp_cols:
            col_lower = col.lower()
            if 'timestamp' in col_lower or 'date' in col_lower or 'time' in col_lower:
                likely_cols.append(col)
        
        # If we found some likely columns, use those instead
        if likely_cols:
            timestamp_cols = likely_cols
    
    return timestamp_cols

def create_ip_port_flow_diagram(df, src_ip_col, dst_ip_col, dst_port_col, filter_dst_ip=None, show_only_top10=False):
    """Create a cyberpunk-styled network flow diagram showing source IPs to destination ports"""
    
    # Validate columns exist in dataframe
    if not all(col in df.columns for col in [src_ip_col, dst_ip_col, dst_port_col]):
        st.error(f"Required columns not found in dataframe")
        return None
        
    # Filter by destination IP if specified
    if filter_dst_ip:
        flow_df = df[df[dst_ip_col] == filter_dst_ip].copy()
        title = f"Network Flows to {filter_dst_ip}"
    else:
        # Take a sample to avoid overcrowding (if no specific dst IP)
        # Get top destination IPs by count
        top_dst_ips = df[dst_ip_col].value_counts().nlargest(1).index.tolist()
        if top_dst_ips:
            flow_df = df[df[dst_ip_col] == top_dst_ips[0]].copy()
            title = f"Network Flows to {top_dst_ips[0]}"
        else:
            flow_df = df.copy()
            title = "Network Flows"

    
    # Prepare data - group by source IP and destination port
    flow_counts = flow_df.groupby([src_ip_col, dst_port_col]).size().reset_index()
    flow_counts.columns = [src_ip_col, dst_port_col, 'count']
    
    # Convert port numbers to strings
    flow_counts[dst_port_col] = flow_counts[dst_port_col].astype(str)
    
    # Calculate total count per source IP for sorting
    src_ip_totals = flow_counts.groupby(src_ip_col)['count'].sum().reset_index()
    src_ip_totals = src_ip_totals.sort_values('count', ascending=False)
    print(src_ip_totals)
    
    # Filter to top 10 source IPs by count if requested
    if show_only_top10:
        top_srcs = src_ip_totals.nlargest(10, 'count')[src_ip_col].tolist()
        flow_counts = flow_counts[flow_counts[src_ip_col].isin(top_srcs)]
    
    # Get unique source IPs and destination ports
    unique_srcs = src_ip_totals[src_ip_col].tolist() # Already sorted by count
    unique_ports = flow_counts[dst_port_col].unique()
    
    # Limit to top 15 sources and top 20 ports by count if too many (and not already limited)
    if len(unique_srcs) > 15 and not show_only_top10:
        unique_srcs = unique_srcs[:15]
        flow_counts = flow_counts[flow_counts[src_ip_col].isin(unique_srcs)]
        
    if len(unique_ports) > 20:
        top_ports = flow_counts.groupby(dst_port_col)['count'].sum().nlargest(20).index.tolist()
        flow_counts = flow_counts[flow_counts[dst_port_col].isin(top_ports)]
        unique_ports = top_ports
    
    # Create position mappings for nodes
    # Source IPs on left (sorted by count from top to bottom)
    src_positions = {ip: (0, i) for i, ip in enumerate(unique_srcs)}
    port_positions = {port: (1, i) for i, port in enumerate(unique_ports)}
    
    # Define cyberpunk color palette
    cyberpunk_colors = [
        '#00f2ff',  # Cyan
        '#ff5900',  # Orange
        '#00ff9d',  # Neon green
        '#ff3864',  # Hot pink
        '#a742f5',  # Purple
        '#ffb000',  # Yellow
        '#36a2eb',  # Blue
        '#ff6384',  # Salmon
        '#29c7ac',  # Teal
        '#ff9e00',  # Amber
        '#00b8d9',  # Light blue
        '#ff5bff',  # Magenta
        '#7dff00',  # Lime
        '#8257e5',  # Indigo
        '#ffc107',  # Gold
        '#00d4b1',  # Turquoise
        '#e052a0',  # Pink
        '#00d0ff',  # Sky blue
        '#ff4081',  # Rose
        '#9c27b0'   # Violet
    ]
    
    # Create color mapping for ports
    color_map = {port: cyberpunk_colors[i % len(cyberpunk_colors)] for i, port in enumerate(unique_ports)}
    
    # Create the figure
    fig = go.Figure()
    
    # Add invisible scatter traces for source IPs (left side)
    fig.add_trace(go.Scatter(
        x=[0] * len(src_positions),
        y=list(range(len(src_positions))),
        mode='markers',
        marker=dict(
            color='rgba(0, 242, 255, 0.9)',
            size=12,
            line=dict(color='rgba(0, 242, 255, 0.5)', width=1),
        ),
        text=list(src_positions.keys()),
        hoverinfo='text',
        name='Source IPs'
    ))
    
    # Add invisible scatter traces for destination ports (right side)
    for i, port in enumerate(unique_ports):
        # Get color for this port
        color = color_map[port]
        
        fig.add_trace(go.Scatter(
            x=[1],
            y=[i],
            mode='markers',
            marker=dict(
                color=color,
                size=12,
                line=dict(color='rgba(255, 255, 255, 0.5)', width=1),
                symbol='square',
            ),
            text=[f"Port: {port}"],
            hoverinfo='text',
            name=f'Port {port}'
        ))
    
    # Add sankey-like flow lines for each connection
    for _, row in flow_counts.iterrows():
        src_ip = row[src_ip_col]
        dst_port = row[dst_port_col]
        count = row['count']
        
        # Skip if source IP is not in our position mapping (might have been filtered)
        if src_ip not in src_positions:
            continue
        
        # Get positions
        src_pos = src_positions[src_ip]
        dst_pos = port_positions[dst_port]
        
        # Calculate line width based on count (minimum 1, maximum 10)
        max_count = flow_counts['count'].max()
        line_width = 1 + 9 * (count / max_count) if max_count > 0 else 1
        
        # Get color for this port
        line_color = color_map[dst_port]
        
        # Add line connecting source IP to destination port
        fig.add_trace(go.Scatter(
            x=[src_pos[0], dst_pos[0]],
            y=[src_pos[1], dst_pos[1]],
            mode='lines',
            line=dict(
                width=line_width,
                color=f'rgba{tuple(int(line_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (0.6,)}'
            ),
            text=f"{src_ip} → Port {dst_port}<br>Count: {count}",
            hoverinfo='text',
            showlegend=False
        ))
    
    # Add source IP labels on left side with count info
    for ip, (x, y) in src_positions.items():
        # Get total count for this IP
        total_count = src_ip_totals[src_ip_totals[src_ip_col] == ip]['count'].values[0]
        
        fig.add_annotation(
            x=x - 0.05,
            y=y,
            text=f"{ip} ({total_count})",  # Add count to label
            showarrow=False,
            xanchor='right',
            font=dict(color='#00f2ff', size=10),
        )
    
    # Add port labels on right side
    for port, (x, y) in port_positions.items():
        # Get total count for this port
        port_total = flow_counts[flow_counts[dst_port_col] == port]['count'].sum()
        
        fig.add_annotation(
            x=x + 0.05,
            y=y,
            text=f"Port {port} ({port_total})",  # Add count to label
            showarrow=False,
            xanchor='left',
            font=dict(color=color_map[port], size=10),
        )
    
    # Update layout with cyberpunk styling
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color='#00f2ff', family='Orbitron'),
            x=0.5,
        ),
        template="plotly_dark",
        plot_bgcolor='rgba(23, 28, 38, 0.8)',
        paper_bgcolor='rgba(23, 28, 38, 0.8)', 
        margin=dict(l=50, r=50, t=50, b=20),
        height=max(400, len(unique_srcs) * 25),  # Adjust height based on number of points
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-0.1, 1.1],  # Add padding
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-1, max(len(unique_srcs), len(unique_ports))],  # Add padding
        ),
        showlegend=False,
        hovermode='closest',
    )
    
    # Add glowing effect with shapes
    fig.update_layout(
        shapes=[
            # Bottom border with gradient
            dict(
                type="rect",
                xref="paper", yref="paper",
                x0=0, y0=0, x1=1, y1=0.02,
                line_width=0,
                fillcolor="rgba(0, 242, 255, 0.3)",
                layer="below"
            ),
            # Top border with gradient
            dict(
                type="rect",
                xref="paper", yref="paper",
                x0=0, y0=0.98, x1=1, y1=1,
                line_width=0,
                fillcolor="rgba(255, 89, 0, 0.3)",
                layer="below"
            )
        ]
    )
    
    # Add a grid effect in the background
    fig.add_shape(
        type="rect",
        xref="paper", yref="paper",
        x0=0, y0=0, x1=1, y1=1,
        line=dict(color="rgba(0,0,0,0)"),
        layer="below",
        fillcolor="rgba(0,0,0,0)",
        opacity=0.1,
    )
    
    # Add header labels
    fig.add_annotation(
        x=0,
        y=-0.5,
        text="SOURCE IPs (sorted by count)",
        showarrow=False,
        xanchor='center',
        font=dict(color='#00f2ff', size=12),
        xref='paper',
        yref='paper'
    )
    
    fig.add_annotation(
        x=1,
        y=-0.5,
        text="DESTINATION PORTS",
        showarrow=False,
        xanchor='center',
        font=dict(color='#ff5900', size=12),
        xref='paper',
        yref='paper'
    )
    
    return fig


def parse_timestamp(df, timestamp_col):
    """Parse timestamp column with improved handling for multiple formats"""
    # Create a copy to avoid warnings about modifying the original dataframe
    df_copy = df.copy()
    
    # First check if column is already datetime
    if pd.api.types.is_datetime64_any_dtype(df_copy[timestamp_col]):
        return df_copy
    
    # Sample the column to identify the format
    sample_values = df_copy[timestamp_col].dropna().astype(str).iloc[:10].tolist()
    
    # Format spécifique: Mar 10 20:26:05
    if any(len(str(val).split()) == 3 and str(val).split()[0] in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"] for val in sample_values):
        try:
            # Essayer d'ajouter l'année courante si elle est absente
            current_year = datetime.datetime.now().year
            
            def add_year_if_needed(ts_str):
                try:
                    if isinstance(ts_str, str):
                        parts = ts_str.split()
                        if len(parts) == 3:  # Format "Mar 10 20:26:05" sans année
                            return f"{parts[0]} {parts[1]} {current_year} {parts[2]}"
                    return ts_str
                except:
                    return ts_str
            
            # Appliquer la transformation et parser
            df_copy[timestamp_col] = df_copy[timestamp_col].apply(add_year_if_needed)
            df_copy[timestamp_col] = pd.to_datetime(df_copy[timestamp_col], format="%b %d %Y %H:%M:%S")
            return df_copy
        except Exception as e:
            st.warning(f"Erreur lors du parsing du format spécial: {str(e)}")
    
    # Try to detect Elasticsearch/Kibana format with '@' symbol
    if any('@' in str(val) for val in sample_values):
        try:
            # Special handling for Kibana format: "Mar 10, 2025 @ 12:42:28.656"
            # First clean up the format to something pandas can understand
            def clean_kibana_timestamp(ts):
                try:
                    if isinstance(ts, str) and '@' in ts:
                        # Replace @ with space for easier parsing
                        return ts.replace('@', '')
                    return ts
                except:
                    return ts
            
            # Apply cleaning function
            df_copy[timestamp_col] = df_copy[timestamp_col].apply(clean_kibana_timestamp)
            
            # Now try to parse with explicit format
            try:
                df_copy[timestamp_col] = pd.to_datetime(df_copy[timestamp_col], format='%b %d, %Y %H:%M:%S.%f')
                return df_copy
            except:
                pass  # Fall through to next method if this fails
        except Exception as e:
            st.warning(f"Special Elasticsearch format handling failed: {str(e)}")
    
    # Try common formats explicitly to avoid format inference issues
    formats_to_try = [
        '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO format with milliseconds and Z
        '%Y-%m-%dT%H:%M:%SZ',     # ISO format without milliseconds with Z
        '%Y-%m-%dT%H:%M:%S.%f',   # ISO format with milliseconds
        '%Y-%m-%dT%H:%M:%S',      # ISO format without milliseconds
        '%Y-%m-%d %H:%M:%S.%f',   # Standard datetime with milliseconds
        '%Y-%m-%d %H:%M:%S',      # Standard datetime
        '%m/%d/%Y %H:%M:%S',      # US format
        '%d/%m/%Y %H:%M:%S',      # European format
        '%Y-%m-%d',               # Just date
        '%m/%d/%Y',               # US date only
        '%d/%m/%Y',               # European date only
        '%b %d, %Y',              # Month name date
        '%B %d, %Y',              # Full month name date
        '%d %b %Y',               # Day first with month name
        '%Y%m%d',                 # Compact date format
        '%b %d, %Y %H:%M:%S',     # Month name with time
        '%b %d, %Y %H:%M:%S.%f',  # Month name with time and milliseconds
        '%b %d %H:%M:%S'          # Format "Mar 10 20:26:05" (sans année)
    ]
    
    for fmt in formats_to_try:
        try:
            df_copy[timestamp_col] = pd.to_datetime(df_copy[timestamp_col], format=fmt)
            return df_copy
        except:
            continue
    
    # If explicit formats fail, try to extract date components with regex
    date_patterns = [
        # Extract ISO-like format
        r'(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})',
        # Extract Elasticsearch format
        r'([A-Za-z]{3}\s\d{1,2},\s\d{4}).*?(\d{2}:\d{2}:\d{2})',
        # Extract format "Mar 10 20:26:05"
        r'([A-Za-z]{3})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})'
    ]
    
    for pattern in date_patterns:
        try:
            # Extract date and time components
            date_match = df_copy[timestamp_col].astype(str).str.extract(pattern)
            if not date_match.iloc[:, 0].isna().all():
                # Combine extracted components
                extracted_datetime = date_match.iloc[:, 0] + ' ' + date_match.iloc[:, 1]
                df_copy[timestamp_col] = pd.to_datetime(extracted_datetime, errors='coerce')
                if not df_copy[timestamp_col].isna().all():
                    return df_copy
        except:
            continue
    
    # Last resort - try pandas default parsing with explicit error handling
    try:
        # Use errors='coerce' to convert unparseable values to NaT
        df_copy[timestamp_col] = pd.to_datetime(df_copy[timestamp_col], errors='coerce')
        
        # Check if conversion worked for at least some values
        if not df_copy[timestamp_col].isna().all():
            # Display a warning about unparseable dates
            na_count = df_copy[timestamp_col].isna().sum()
            if na_count > 0:
                percentage = (na_count / len(df_copy)) * 100
                st.warning(f"⚠️ {na_count} values ({percentage:.1f}%) in column '{timestamp_col}' couldn't be parsed as dates and were replaced with NaT.")
            return df_copy
    except Exception as e:
        pass
    
    # If all else fails, show helpful error message with example values
    st.error(f"""
    Could not parse date format in '{timestamp_col}'. 
    Example values: {', '.join(str(val) for val in sample_values[:3])}
    
    Please select a different timestamp column or ensure the data is in a standard date format.
    """)
    
    # Return original dataframe but with warning
    return df




@st.cache_data(ttl=3600)
def cached_extract_ips(df):
    """Version mise en cache de extract_ips pour améliorer les performances"""
    return extract_ips(df)

@st.cache_data
def filter_df_by_time_cached(df, timestamp_col, start_time, end_time):
    """Version mise en cache du filtre temporel"""
    return filter_df_by_time(df, timestamp_col, start_time, end_time)

@st.cache_data
def detect_timestamp_cols_cached(df):
    """Version mise en cache de la détection des colonnes timestamp"""
    return detect_timestamp_cols(df)

@st.cache_data
def cached_parse_timestamp(df, timestamp_col):
    """Version mise en cache du parsing de timestamp"""
    return parse_timestamp(df, timestamp_col)

def main():
    apply_custom_css()
    apply_border_glitch_effect() # Apply glitch effect to metrics and plots
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
    # Create tabs for different sections (like Grafana)
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Exploration", "⚙️ Settings"])
    
    with tab1:
        # File upload section with cyberpunk styling
        st.markdown("<div class='grafana-panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-header'>DATA SOURCE</div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "DROP CSV/PARQUET FILE",
            type=["csv", "parquet"],
            help="Supported file formats: CSV and Parquet"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
    
        if uploaded_file is not None:
            try:
                # Stocker un ID unique basé sur le nom et la taille du fichier pour la mise en cache
                file_id = f"{uploaded_file.name}_{uploaded_file.size}"
                
                # Vérifier si le fichier est en cache
                if "file_id" not in st.session_state or st.session_state.file_id != file_id:
                    # Nouveau fichier chargé, mettre à jour l'ID et effacer les états précédents
                    st.session_state.file_id = file_id
                    if "filtered_df" in st.session_state:
                        del st.session_state.filtered_df
                    if "time_filter_applied" in st.session_state:
                        st.session_state.time_filter_applied = False
                        
                # Charger les données avec cache
                df = cached_load_data(uploaded_file)
                
                if df is not None:
                    # Store the original dataframe in the session state when first uploading
                    if "original_df" not in st.session_state:
                        st.session_state.original_df = df
                        
                    # Initialize filtered_df in session state if not present
                    if "filtered_df" not in st.session_state:
                        st.session_state.filtered_df = df
                        
                    # Initialize time filter applied flag
                    if "time_filter_applied" not in st.session_state:
                        st.session_state.time_filter_applied = False
                    
                    # Detect timestamp columns with cache
                    timestamp_cols = detect_timestamp_cols_cached(df)
                    
                    # Create time selector panel if timestamp columns exist
                    if timestamp_cols:
                        st.markdown("<div class='grafana-panel'>", unsafe_allow_html=True)
                        
                        # Add timestamp column selector
                        if "timestamp_col" not in st.session_state and timestamp_cols:
                            st.session_state.timestamp_col = timestamp_cols[0]
                            
                        timestamp_col = st.selectbox(
                            "Select timestamp column",
                            timestamp_cols,
                            index=timestamp_cols.index(st.session_state.timestamp_col) if st.session_state.timestamp_col in timestamp_cols else 0,
                            key="timestamp_col_select",
                            on_change=lambda: setattr(st.session_state, 'timestamp_col', st.session_state.timestamp_col_select)
                        )
                        
                        # Define refresh callback function
                        def refresh_data():
                            """Function to refresh data based on time filter"""
                            st.session_state.time_filter_applied = True
                            
                            # Get original dataframe and apply time filter
                            original_df = st.session_state.original_df
                            filtered_df = filter_df_by_time(original_df, st.session_state.timestamp_col, 
                                                            st.session_state.start_time, st.session_state.end_time)
                            
                            # Store filtered dataframe in session state
                            st.session_state.filtered_df = filtered_df
                        
                        # Add time range selector with refresh callback
                        start_time, end_time, time_unit, time_value, refresh_pressed = time_selector(on_refresh_callback=refresh_data)
                        
                        # Store time range in session state
                        st.session_state.start_time = start_time
                        st.session_state.end_time = end_time
                        
                        # Use filtered_df if refresh was pressed or time filter was previously applied
                        # Otherwise use the original dataframe
                        if refresh_pressed or st.session_state.time_filter_applied:
                            if "cached_filtered_key" not in st.session_state:
                                st.session_state.cached_filtered_key = f"{timestamp_col}_{start_time}_{end_time}"
                            else:
                                # Vérifier si les paramètres de filtre ont changé
                                new_key = f"{timestamp_col}_{start_time}_{end_time}"
                                if new_key != st.session_state.cached_filtered_key:
                                    st.session_state.cached_filtered_key = new_key
                                    # Appliquer le nouveau filtre
                                    st.session_state.filtered_df = filter_df_by_time_cached(df, timestamp_col, start_time, end_time)
                            
                            display_df = st.session_state.filtered_df
                        else:
                            display_df = df
                        
                        # Create time histogram to show data distribution
                        if len(display_df) > 0 and timestamp_col in display_df.columns:
                            # Convert to datetime if not already
                            if not pd.api.types.is_datetime64_any_dtype(display_df[timestamp_col]):
                                display_df = parse_timestamp(display_df.copy(), timestamp_col)
                            
                            # Create time histogram
                            fig = px.histogram(
                                display_df, 
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
                                create_metric_card("FILTERED ROWS", f"{len(display_df):,}")
                            with data_metrics_cols[1]:
                                percent_kept = round((len(display_df) / len(df)) * 100, 1)
                                create_metric_card("% OF TOTAL", f"{percent_kept}%")
                            with data_metrics_cols[2]:
                                create_metric_card("START TIME", f"{start_time.strftime('%H:%M:%S')}")
                            with data_metrics_cols[3]:
                                create_metric_card("END TIME", f"{end_time.strftime('%H:%M:%S')}")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Use display_df for all subsequent operations
                        df = display_df
                    
                    # Rest of your code continues unchanged, just make sure to use the df variable
                    # which now contains either filtered_df or the original based on refresh button
                    
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
    
                    # Remplacez la section qui affiche la carte dans la fonction main()

                    if geoip_process:
                        with st.spinner("Extracting IP addresses and looking up locations..."):
                            # Add a cool cyberpunk banner for the processing
                            st.markdown("""
                            <div style='background-color: #0a0f19; padding: 15px; border-radius: 3px; 
                                border: 1px solid #00f2ff; box-shadow: 0 0 20px rgba(0, 242, 255, 0.5);'>
                                <div style='display: flex; align-items: center; justify-content: center;'>
                                    <div style='font-family: "Orbitron", sans-serif; font-size: 20px; color: #00f2ff; 
                                        text-shadow: 0 0 10px rgba(0, 242, 255, 0.7); letter-spacing: 3px;'>
                                        CYBER THREAT INTELLIGENCE
                                    </div>
                                </div>
                                <div style='height: 2px; background: linear-gradient(90deg, rgba(0,0,0,0), #00f2ff, rgba(0,0,0,0)); 
                                    margin: 10px 0; animation: pulse 2s infinite;'></div>
                                <style>
                                    @keyframes pulse {
                                        0% { opacity: 0.4; }
                                        50% { opacity: 1; }
                                        100% { opacity: 0.4; }
                                    }
                                </style>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Extract IP data
                            src_locations, dst_locations, flows = cached_extract_ips(df)
                            
                            if src_locations or dst_locations:
                                st.success(f"✅ Found {len(src_locations) if src_locations else 0} source IPs and {len(dst_locations) if dst_locations else 0} destination IPs with geolocation data.")
                                
                                # Create cyberpunk-styled threat map header
                                st.markdown("""
                                <div style='margin: 20px 0; text-align: center;'>
                                    <div style='font-family: "Orbitron", sans-serif; font-size: 24px; font-weight: bold;
                                        background: linear-gradient(90deg, #00f2ff, #ff5900);
                                        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                                        text-shadow: 0 0 5px rgba(0, 242, 255, 0.5); letter-spacing: 2px;'>
                                        GLOBAL ATTACK VECTOR MAP
                                    </div>
                                    <div style='font-family: monospace; color: #00ff9d; margin-top: 5px;'>
                                        Real-time visualization of network attack flows
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Create and display map with performance optimizations
                                fig = create_ip_map(src_locations, dst_locations, flows)

                                # Display chart with specific configuration to optimize performance
                                st.plotly_chart(fig, use_container_width=True, config={
                                    'displayModeBar': True,
                                    'modeBarButtonsToRemove': [
                                        'select2d', 'lasso2d', 'hoverClosestGeo', 
                                        'autoScale2d', 'resetScale2d', 'toggleHover'
                                    ],
                                    'displaylogo': False,
                                    'scrollZoom': True,
                                    'responsive': True,
                                    'staticPlot': False,  # Set to True for even better performance but loses interactivity
                                })

                                # Add performance note
                                st.markdown("""
                                <div style="background-color: #181b24; padding: 10px; border-radius: 3px; margin-top: 5px;">
                                    <span style="color: #00f2ff; font-size: 0.8rem;">💡 <strong>Performance Tip:</strong> 
                                    If the map is lagging, try switching between projection types using the buttons above the map.
                                    The Globe view shows accurate paths while the Flat view may be faster.</span>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Show flow statistics with enhanced styling
                                if flows:
                                    st.markdown("""
                                    <div style='margin-top: 25px; margin-bottom: 15px;'>
                                        <div style='font-family: "Orbitron", sans-serif; font-size: 20px; color: #00f2ff; 
                                            text-shadow: 0 0 10px rgba(0, 242, 255, 0.5); letter-spacing: 2px;'>
                                            TRAFFIC FLOW INTELLIGENCE
                                        </div>
                                        <div style='height: 2px; background: linear-gradient(90deg, rgba(0,0,0,0), #00f2ff, rgba(0,0,0,0)); 
                                            margin: 10px 0;'></div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Create DataFrame from flows
                                    flow_df = pd.DataFrame(flows)
                                    
                                    # Group by country pairs
                                    country_flows = flow_df.groupby(['src_country', 'dst_country'])['count'].sum().reset_index()
                                    country_flows = country_flows.sort_values('count', ascending=False)
                                    
                                    # Group by ISP pairs for broader view
                                    isp_flows = flow_df.groupby(['src_isp', 'dst_isp'])['count'].sum().reset_index()
                                    isp_flows = isp_flows.sort_values('count', ascending=False)
                                    
                                    # Create metrics with enhanced styling
                                    metric_cols = st.columns(4)
                                    with metric_cols[0]:
                                        create_metric_card("TOTAL FLOWS", f"{len(flows)}")
                                    with metric_cols[1]:
                                        create_metric_card("COUNTRIES", f"{country_flows['src_country'].nunique() + country_flows['dst_country'].nunique()}")
                                    with metric_cols[2]:
                                        create_metric_card("SOURCE IPs", f"{len(src_locations) if src_locations else 0}")
                                    with metric_cols[3]:
                                        create_metric_card("DEST IPs", f"{len(dst_locations) if dst_locations else 0}")
                                    
                                    # Show top flows with enhanced styling
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown("""
                                        <div style='font-family: "Orbitron", sans-serif; color: #ff5900; 
                                            text-shadow: 0 0 5px rgba(255, 89, 0, 0.5); margin-bottom: 10px;'>
                                            TOP COUNTRY ROUTES
                                        </div>
                                        """, unsafe_allow_html=True)
                                        st.dataframe(country_flows.head(10), use_container_width=True)
                                    
                                    with col2:
                                        st.markdown("""
                                        <div style='font-family: "Orbitron", sans-serif; color: #00ff9d; 
                                            text-shadow: 0 0 5px rgba(0, 255, 157, 0.5); margin-bottom: 10px;'>
                                            TOP ISP CONNECTIONS
                                        </div>
                                        """, unsafe_allow_html=True)
                                        st.dataframe(isp_flows.head(10), use_container_width=True)
                            else:
                                st.error("No valid IP addresses with geolocation data found. Please check your IP columns.")
                
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                else:
                    st.error("Unsupported file format. Please upload a CSV or Parquet file.")
            except Exception as e:
                st.error(f"Error loading data: {str(e)}")

    fig = px.histogram(
    display_df, 
    x=timestamp_col,
    nbins=50,
    color_discrete_sequence=["#ff5900", "#00f2ff"]  # Alternating colors
)

    # Apply cyberpunk styling
    fig = cyberpunk_plot_layout(fig, height=150)

    st.plotly_chart(fig, use_container_width=True)
        # Dans la section où vous créez le graphique empilé
    st.markdown("<div class='grafana-panel'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-header'>TEMPORAL EVENT DISTRIBUTION</div>", unsafe_allow_html=True)

    # Initialiser les clés de session pour maintenir l'état entre les rafraîchissements
    if "selected_time_col" not in st.session_state:
        st.session_state.selected_time_col = timestamp_cols[0] if timestamp_cols else None
    if "selected_group_col" not in st.session_state:
        # Initialisation par défaut pour le group_by
        category_cols = [col for col in df.columns if col != st.session_state.selected_time_col and 
                        (df[col].dtype == 'object' or 
                        df[col].dtype == 'category' or 
                        df[col].nunique() <= 20)]
        
        if not category_cols:
            category_cols = [col for col in df.columns if col != st.session_state.selected_time_col and
                            df[col].dtype in ['int64', 'float64'] and
                            df[col].nunique() <= 20]
        
        st.session_state.selected_group_col = category_cols[0] if category_cols else None
        st.session_state.category_cols = category_cols

    # Fonctions de callback pour mettre à jour les variables de session sans rafraîchir
    def update_time_col():
        st.session_state.selected_time_col = st.session_state.time_axis_col_select
        
    def update_group_col():
        st.session_state.selected_group_col = st.session_state.group_by_col_select

    # Interface utilisateur avec callbacks
    col1, col2 = st.columns(2)

    with col1:
        selected_time_col = st.selectbox(
            "Time Axis",
            timestamp_cols,
            index=timestamp_cols.index(st.session_state.selected_time_col) if st.session_state.selected_time_col in timestamp_cols else 0,
            key="time_axis_col_select",
            on_change=update_time_col
        )

    with col2:
        # Utiliser les colonnes déjà identifiées stockées dans l'état de session
        category_cols = st.session_state.category_cols
        
        if category_cols:
            selected_group_col = st.selectbox(
                "Group By",
                category_cols,
                index=category_cols.index(st.session_state.selected_group_col) if st.session_state.selected_group_col in category_cols else 0,
                key="group_by_col_select",
                on_change=update_group_col
            )

    # Utiliser les variables stockées dans la session pour créer le graphique
    stacked_fig = create_stacked_area_chart(df, st.session_state.selected_time_col, st.session_state.selected_group_col)
                
    if stacked_fig:
        st.plotly_chart(stacked_fig, use_container_width=True)
    else:
        st.warning("Could not create stacked area chart with the selected columns")
        
    st.markdown("</div>", unsafe_allow_html=True)
            # IP port flow visualization
    st.markdown("<div class='grafana-panel'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-header'>IP-PORT FLOW ANALYSIS</div>", unsafe_allow_html=True)

    # Check if we have IP and port columns
    ip_cols = [col for col in df.columns if 'ip' in col.lower()]
    port_cols = [col for col in df.columns if 'port' in col.lower()]

    if ip_cols and port_cols:
        # Let user select columns
        col1, col2 = st.columns(2)
        
        with col1:
            src_ip_col = st.selectbox(
                "Source IP",
                [col for col in ip_cols if 'src' in col.lower() or 'source' in col.lower()],
                key="src_ip_col_flow"
            )
        
        with col2:
            dst_ip_col = st.selectbox(
                "Destination IP",
                [col for col in ip_cols if 'dst' in col.lower() or 'dest' in col.lower()],
                key="dst_ip_col_flow"
            )
        
        col3, col4 = st.columns(2)
        with col3:
            dst_port_col = st.selectbox(
                "Destination Port",
                port_cols,
                key="dst_port_col_flow"
            )
        
        with col4:
            # Get top destination IPs by count for selection
            top_dst_ips = df[dst_ip_col].value_counts().nlargest(10).index.tolist()
            selected_dst_ip = st.selectbox(
                "Filter Destination IP",
                ["All"] + top_dst_ips,
                key="selected_dst_ip"
            )
        
        # Add options row
        col_opts1, col_opts2 = st.columns(2)
        with col_opts1:
            show_top10_only = st.checkbox("Show only top 10 source IPs by traffic volume", 
                                        value=False, 
                                        key="show_top10")
        
        # Create visualization
        if st.button("🔄 Generate Flow Diagram", key="gen_flow_diagram"):
            with st.spinner("Generating IP-Port flow diagram..."):
                filter_ip = None if selected_dst_ip == "All" else selected_dst_ip
                flow_fig = create_ip_port_flow_diagram(
                    df, 
                    src_ip_col, 
                    dst_ip_col, 
                    dst_port_col,
                    filter_dst_ip=filter_ip,
                    show_only_top10=show_top10_only
                )
                
                if flow_fig:
                    st.plotly_chart(flow_fig, use_container_width=True)
                    
                    # Add explanatory text with cyberpunk styling
                    st.markdown("""
                    <div style='background-color: #181b24; padding: 15px; border-radius: 3px; 
                        border: 1px solid rgba(255, 89, 0, 0.3); margin-top: 10px;'>
                        <p style='margin: 0;'>
                            <span style='color: #ff5900; font-weight: bold;'>NETWORK FLOW ANALYSIS:</span>
                            This diagram visualizes network traffic patterns from source IPs (left) to destination ports (right).
                            Line thickness represents connection frequency, and colors indicate different destination ports.
                            <br><br>
                            <span style='color: #00f2ff; font-size: 0.9rem;'>
                                Hover over connections to see detailed traffic counts. Source IPs are sorted by total connection volume.
                            </span>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("Could not create flow diagram with selected columns")
    else:
        st.info("No IP address or port columns detected in this dataset.")

    st.markdown("</div>", unsafe_allow_html=True)
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
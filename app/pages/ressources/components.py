import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import ipaddress
import socket


 
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
        # Convert to pandas DataFrame instead of polars
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
        # Convert to pandas DataFrame instead of polars
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



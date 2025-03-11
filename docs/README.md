# 🚀 OOPSISE | Advanced Network Data Analytics Platform

## 📊 Overview
OOPSISE is a cyberpunk-styled data analytics platform specifically designed for network data analysis. Built with Streamlit, this application provides powerful data visualization and machine learning capabilities with a unique retrofuturistic interface inspired by Grafana and Kibana.

## ✨ Key Features
- **Interactive Data Dashboard**: Visualize complex network data with cyberpunk-styled charts and metrics
- **Time-based Analysis**: Filter data with Kibana-like time selectors (last N minutes/hours/days)
- **IP Geolocation**: Map source and destination IP addresses globally
- **Network Flow Analysis**: Visualize traffic patterns between IPs and ports
- **Anomaly Detection**: CRISP-DM based machine learning to identify unusual patterns
- **Multi-format Support**: Import data from CSV, Parquet, and Excel files
- **Responsive Design**: Optimized for both desktop and mobile viewing

## 🔧 Installation

### Prerequisites
- Python 3.11+
- Docker 

### Method 1: Local Installation
```bash
# Clone the repository
git clone https://github.com/alexisgabrysch/OOPSISE.git
cd OOPSISE

# Install dependencies
pip install -r requirements.txt

# Run the application
cd app
streamlit run app.py
```

### Method 2: Docker Installation
```bash
# Clone the repository
git clone https://github.com/alexisgabrysch/OOPSISE.git
cd OOPSISE

# Build the Docker image
docker build -t oopsise .

# Run the Docker container
docker run -p 8501:8501 oopsise
```

The application will be available at [http://localhost:8501](http://localhost:8501)

## 📚 Usage Guide

### Uploading Data
1. Navigate to the Dashboard page
2. Use the file uploader to import your network data (CSV, Parquet, or Excel)
3. The system will automatically detect column headers and data formats

### Time-based Analysis
1. Select a timestamp column from your data
2. Choose a time range preset (last 15 minutes, last hour, last day, etc.) or a custom range
3. Click the Refresh button to apply the time filter

### Network Visualization
- **IP Geolocation Map**: Visualizes source and destination IPs on a world map
- **Flow Analysis**: Shows connections between source IPs and destination ports
- **Stacked Area Charts**: Displays traffic patterns over time
- **Metric Cards**: Shows key statistics in Grafana-style panels

### Machine Learning Analysis
The platform integrates CRISP-DM methodology for advanced analytics:
- **Clustering**: Segments traffic patterns using K-means
- **Anomaly Detection**: Identifies outliers with Isolation Forest
- **Dimensionality Reduction**: Reduces complexity with PCA

## 🔒 Security Features
- No data is stored on external servers
- All processing happens locally
- Compatible with sensitive network logs

## 🖥️ System Architecture
```
app/
├── app.py            # Main application entry point
├── .streamlit/       # Streamlit configuration
├── data/             # Sample datasets
├── ml/               # Machine learning models
├── pages/            # Application pages
│   ├── dashboard.py  # Main analytics dashboard
│   └── ressources/   # Shared components
└── utils/            # Utility functions
```

## 🛠️ Development

### Adding New Visualizations
1. Create a new visualization function in the dashboard.py file
2. Apply the cyberpunk styling using the provided helper functions
3. Add the visualization to the appropriate tab in the main interface

### Extending Machine Learning Capabilities
The `ml/` directory contains the CRISP-DM analysis framework that can be extended with additional models.

## 🤝 Contributing
Contributions to OOPSISE are welcome! Please follow these steps:
1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request


## 👥 Team
- Alexis Gabrysch
- Antoine Oruezabala


import os
from flask import Flask, render_template, jsonify, send_from_directory
import requests

app = Flask(__name__)

# Configuration for stream details
class StreamConfig:
    # GitHub raw file URL for stream details
    STREAM_DETAILS_URL = 'https://raw.githubusercontent.com/seeubot/bots/refs/heads/main/stream_details.json'
    
    # Local cache file to store stream details
    CACHE_FILE = 'stream_details.json'

def fetch_stream_details():
    """
    Fetch stream details from GitHub or local cache
    """
    try:
        # Attempt to fetch from GitHub
        response = requests.get(StreamConfig.STREAM_DETAILS_URL)
        response.raise_for_status()
        stream_details = response.json()
        
        # Cache the details locally
        with open(StreamConfig.CACHE_FILE, 'w') as f:
            import json
            json.dump(stream_details, f)
        
        return stream_details
    except Exception as e:
        print(f"Error fetching from GitHub: {e}")
        
        # Fallback to local cache if available
        try:
            with open(StreamConfig.CACHE_FILE, 'r') as f:
                import json
                return json.load(f)
        except FileNotFoundError:
            # If no local cache, return default/empty details
            return {
                "file": "",
                "keyId": "",
                "key": ""
            }

@app.route('/')
def index():
    """
    Main route to serve the video player page
    """
    return render_template('index.html')

@app.route('/stream-details')
def get_stream_details():
    """
    API endpoint to retrieve stream details
    """
    stream_details = fetch_stream_details()
    return jsonify(stream_details)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """
    Serve static files (if needed)
    """
    return send_from_directory('static', filename)

# Deployment configuration
def create_app():
    """
    Create and configure the Flask application
    """
    return app

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',  # Listen on all available interfaces
        port=5000,       # Default port
        debug=True       # Enable debug mode for development
    )

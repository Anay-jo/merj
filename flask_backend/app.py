#!/usr/bin/env python3
"""
Flask Backend for Merj Merge Conflict Tool
Receives diff data from merj.js and processes it
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for requests from Node.js frontend

@app.route('/api/data', methods=['POST'])
def receive_diff_data():
    """
    POST endpoint to receive diff data from merj.js
    Expected JSON structure:
    {
        "lbd": [...],  # Local vs Base diff
        "rbd": [...],  # Remote vs Base diff  
        "lrd": [...]   # Local vs Remote diff
    }
    """
    try:
        # Get JSON data from request body
        data = request.get_json()
        # Validate that data was received
        if not data:
            return jsonify({
                'error': 'No JSON data received',
                'status': 'error'
            }), 400

        remote_vs_base_diff = data['rbd']
        local_vs_base_diff = data['lbd']        



        # Return success response
        return jsonify({
            'message': 'Diff data received successfully',
            'status': 'success',
            'data_keys': list(data.keys()) if isinstance(data, dict) else 'not_a_dict'
        }), 200
        
    except Exception as e:
        # Handle any errors
        print(f"❌ Error processing request: {str(e)}")
        return jsonify({
            'error': f'Failed to process request: {str(e)}',
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

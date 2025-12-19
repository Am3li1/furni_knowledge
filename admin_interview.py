# app.py - Dokploy optimized
import os
from flask import Flask, request, jsonify, session, render_template_string
import json
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dokploy-secret-123')

# Configuration for Dokploy
app.config.update(
    PREFERRED_URL_SCHEME='https',
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Simple health check endpoint (REQUIRED for Dokploy)
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "furniture-admin"}), 200

# Root endpoint
@app.route('/')
def home():
    return jsonify({
        "service": "Furniture Admin Interview System",
        "status": "running",
        "admin_url": "/admin",
        "health_check": "/health"
    })

# Your existing admin interview code continues here...
# [Keep all your existing routes: /admin, /admin/login, /admin/chat, etc.]

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # debug=False for production
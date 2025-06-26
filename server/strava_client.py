#!/usr/bin/env python3
"""
Strava API client for running-heatmap.
Handles OAuth2 authentication and data fetching.
"""

import os
import json
import configparser
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests

CONFIG_FILE = 'config.ini'
TOKENS_FILE = 'strava_tokens.json'

class StravaClient:
    def __init__(self):
        self.config = configparser.ConfigParser()
        if not os.path.exists(CONFIG_FILE):
            raise FileNotFoundError(f"Configuration file '{CONFIG_FILE}' not found. Please create it from the template.")
        self.config.read(CONFIG_FILE)
        
        self.client_id = self.config.get('strava', 'client_id')
        self.client_secret = self.config.get('strava', 'client_secret')
        self.tokens = self.load_tokens()

    def load_tokens(self):
        if os.path.exists(TOKENS_FILE):
            with open(TOKENS_FILE, 'r') as f:
                return json.load(f)
        return None

    def save_tokens(self, tokens):
        with open(TOKENS_FILE, 'w') as f:
            json.dump(tokens, f, indent=2)
        self.tokens = tokens

    def is_authenticated(self):
        return self.tokens is not None and self.tokens.get('access_token')

    def get_authorization_url(self):
        return (
            f"https://www.strava.com/oauth/authorize?"
            f"client_id={self.client_id}"
            "&response_type=code"
            "&redirect_uri=http://localhost:8000"
            "&approval_prompt=force"
            "&scope=read,activity:read_all"
        )

    def exchange_code_for_tokens(self, code):
        response = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code'
            }
        )
        response.raise_for_status()
        self.save_tokens(response.json())
        print("✅ Successfully exchanged code for tokens.")

    def refresh_access_token(self):
        if not self.tokens or 'refresh_token' not in self.tokens:
            raise Exception("No refresh token available. Please re-authorize.")

        print("🔄 Refreshing access token...")
        response = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': self.tokens['refresh_token']
            }
        )
        response.raise_for_status()
        self.save_tokens(response.json())
        print("✅ Token refreshed successfully.")

    def get_activities(self, after_timestamp=None):
        if not self.is_authenticated():
            raise Exception("Not authenticated. Please run the authorization first.")

        if self.tokens['expires_at'] < time.time():
            self.refresh_access_token()

        headers = {'Authorization': f"Bearer {self.tokens['access_token']}"}
        params = {'per_page': 100}
        if after_timestamp:
            params['after'] = after_timestamp

        activities = []
        page = 1
        while True:
            params['page'] = page
            response = requests.get("https://www.strava.com/api/v3/activities", headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            activities.extend(data)
            page += 1
        
        return activities

def run_initial_authorization():
    """Guides the user through the initial Strava authorization process."""
    client = StravaClient()
    
    if client.is_authenticated():
        print("✅ You are already authenticated.")
        return

    auth_url = client.get_authorization_url()
    print("Your browser should open for Strava authorization.")
    print(f"If it doesn't, please open this URL: {auth_url}")
    webbrowser.open(auth_url)

    class OAuthCallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed_path = urlparse(self.path)
            query = parse_qs(parsed_path.query)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            if 'code' in query:
                self.wfile.write(b"<h1>Authorization successful!</h1><p>You can close this window.</p>")
                self.server.authorization_code = query['code'][0]
            else:
                self.wfile.write(b"<h1>Authorization failed.</h1><p>Please try again.</p>")
                self.server.authorization_code = None

    httpd = HTTPServer(('localhost', 8000), OAuthCallbackHandler)
    httpd.authorization_code = None
    print("\nWaiting for authorization code from Strava... (check your browser)")
    httpd.handle_request() # Handle one request and close

    if httpd.authorization_code:
        print("✅ Authorization code received.")
        client.exchange_code_for_tokens(httpd.authorization_code)
    else:
        print("❌ Authorization failed. No code received.")

if __name__ == '__main__':
    print("--- Strava Client Setup ---")
    run_initial_authorization()

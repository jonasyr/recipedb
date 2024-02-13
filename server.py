from flask import Flask, redirect, request, session, render_template
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
from datetime import datetime
from dateutil.parser import parse
import json

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configuration for Google OAuth2
CLIENT_ID = '555781865388-1i0hdu3l3cii51lqdh3l5jhk3g5dq6nk.apps.googleusercontent.com'
CLIENT_SECRET = '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'
SCOPE = 'https://www.googleapis.com/auth/spreadsheets.readonly'
REDIRECT_URI = 'http://localhost:5000/oauth2callback'
SPREADSHEET_ID = '1s5MgDM2lvUJllORM7tY1uyilPBQ8Wrjwc6v2Ztl7AJ4'
RANGE_NAME = 'YOUR_RANGE_NAME'

app = Flask(__name__)
app.secret_key = 'YOUR_SECRET_KEY'  # Replace with your secret key

# OAuth2 Web Server Flow
flow = Flow.from_client_config(
    client_config={
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    },
    scopes=[SCOPE],
    redirect_uri=REDIRECT_URI
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    return redirect(authorization_url)

@app.route("/oauth2callback")
def oauth2callback():
    flow.fetch_token(authorization_response=request.url)
    
    credentials = flow.credentials
    if not credentials.valid:
        return "Authentication failed."

    session['credentials'] = flow.credentials.to_json()
    return redirect("/recipes")

@app.route("/recipes")
def all_recipes():
    cred_info = json.loads(session['credentials'])
    
    # Convert 'expiry' back to a timezone-aware datetime object
    if 'expiry' in cred_info:
        cred_info['expiry'] = parse(cred_info['expiry'])
    
    credentials = Credentials(**cred_info)
    
    # Your existing code for checking credentials and refreshing tokens
    if not credentials.valid:
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            return redirect("/login")
    
    session['credentials'] = credentials.to_json()
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    
    recipes = [{"name": row[0], "description": row[1], "ingredients": row[2]} for row in values]  # Adjust as needed
    
    return render_template("recipes.html", recipes=recipes)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

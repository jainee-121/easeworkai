import os
import base64
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from datetime import datetime
import json
from typing import List, Dict, Any, Optional

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            # Use the exact redirect URI that Google expects
            flow.redirect_uri = 'http://localhost:8080/'
            creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def get_email_data(service, message_id: str) -> Dict[str, Any]:
    message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    
    headers = message['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
    sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
    date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
    
    try:
        # Parse the email date
        timestamp = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
        # Format the timestamp in a user-readable format
        formatted_date = timestamp.strftime('%B %d, %Y %I:%M %p')
    except:
        timestamp = datetime.now()
        formatted_date = timestamp.strftime('%B %d, %Y %I:%M %p')
    
    # Get attachments
    attachments = []
    if 'parts' in message['payload']:
        for part in message['payload']['parts']:
            if part.get('filename'):
                attachment = {
                    'id': part['body'].get('attachmentId'),
                    'filename': part['filename'],
                    'mimeType': part['mimeType']
                }
                attachments.append(attachment)
    
    return {
        'sender': sender,
        'subject': subject,
        'timestamp': formatted_date,
        'attachments': attachments
    }

def download_attachment(service, message_id: str, attachment_id: str) -> bytes:
    attachment = service.users().messages().attachments().get(
        userId='me',
        messageId=message_id,
        id=attachment_id
    ).execute()
    
    return base64.urlsafe_b64decode(attachment['data'])

def fetch_emails(service, max_results: int = 10) -> List[Dict[str, Any]]:
    results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    messages = results.get('messages', [])
    
    emails = []
    for message in messages:
        email_data = get_email_data(service, message['id'])
        emails.append(email_data)
    
    return emails

def get_email_with_attachment(service, message_id: str, attachment_id: str) -> Dict[str, Any]:
    email_data = get_email_data(service, message_id)
    attachment_data = download_attachment(service, message_id, attachment_id)
    
    return {
        **email_data,
        'attachment_data': base64.b64encode(attachment_data).decode('utf-8')
    } 
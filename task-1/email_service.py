import os
import base64
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime
from typing import List, Dict, Any

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Get authenticated Gmail service."""
    creds = None
    
    # Load existing credentials if available
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            flow.redirect_uri = 'http://localhost:8080/'
            creds = flow.run_local_server(port=8080)
            
        # Save credentials for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def get_email_data(service, message_id: str) -> Dict[str, Any]:
    """Get detailed email data."""
    message = service.users().messages().get(
        userId='me', 
        id=message_id, 
        format='full'
    ).execute()
    
    # Extract headers
    headers = message['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
    sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
    date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
    
    # Parse and format date
    try:
        timestamp = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
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
    """Download email attachment."""
    attachment = service.users().messages().attachments().get(
        userId='me',
        messageId=message_id,
        id=attachment_id
    ).execute()
    
    return base64.urlsafe_b64decode(attachment['data'])

def fetch_emails(service, max_results: int = 10) -> List[Dict[str, Any]]:
    """Fetch list of emails."""
    results = service.users().messages().list(
        userId='me', 
        maxResults=max_results
    ).execute()
    messages = results.get('messages', [])
    
    return [get_email_data(service, message['id']) for message in messages]

def get_email_with_attachment(service, message_id: str, attachment_id: str) -> Dict[str, Any]:
    """Get email with attachment data."""
    email_data = get_email_data(service, message_id)
    attachment_data = download_attachment(service, message_id, attachment_id)
    
    return {
        **email_data,
        'attachment_data': base64.b64encode(attachment_data).decode('utf-8')
    } 
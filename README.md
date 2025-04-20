# EaseWorkAI: TASK-1

Task-1 is an application that connects to the Gmail API to fetch, process, and serve emails and attachments through authenticated API endpoints.

### Reference and additional tool used:
- https://github.com/jainee-121/e-commerce
- CusorAI(for debugging)

## Setup Instructions

### Prerequisites

- Python 3.7+
- PostgreSQL database
- Gmail API credentials (`credentials.json`)

### Environment Setup

1. Clone the repository and navigate to the project root.
2. Create a `.env` file with the following variables:
   ```
   DATABASE_URL=your_postgresql_database_url
   SECRET_KEY=your_secret_key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

3. Place your `credentials.json` (Gmail API) in the project root directory.

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the application once to generate `token.pickle` for Gmail API authentication:
   ```bash
   uvicorn main:app --reload
   ```

---

## API Endpoints

### Authentication

#### POST `/token`
Login endpoint to obtain a JWT access token.  
**Request body:**
```json
{
  "email": "your_email",
  "password": "your_password"
}
```

#### POST `/logout`
Logs out the current user.  
**Authentication required**

---

### User Management

#### POST `/users`
Registers a new user.  
**Request body:**
```json
{
  "username": "new_user",
  "email": "user_email",
  "password": "secure_password",
  "confirm-password":"confirm-password"
}
```

---

### Email Operations

#### GET `/emails`
Fetch a list of emails.  
**Query Parameters:**
- `max_results`: Maximum number of emails to retrieve (default: 10)  
**Authentication required**

#### GET `/emails/{message_id}`
Fetch details of a specific email.  
**Authentication required**

#### GET `/emails/{message_id}/attachments/{attachment_id}`
Download a specific email attachment.  
Returns the attachment as a stream.  
**Authentication required**

#### GET `/emails/{message_id}/attachments/{attachment_id}/base64`
Download a specific email attachment in base64 format.  
**Authentication required**

---

## Database Structure

### User Model
Defined in `models.py` and includes fields like:
```python
class User:
    id: Integer (Primary Key)
    name: String
    email: String (Unique)
    hashed_password: String
    permissions: String (JSON)
    is_active: Boolean
    created_at: DateTime
    last_login: DateTime
```

### Email Schemas
```python
class Email:
    message_id: String
    subject: String
    sender: String
    timestamp: DateTime
    attachments: List[Attachment]

class Attachment:
    id: String
    filename: String
    mimeType: String
```
---

## Example Test Cases

### User Registration
```python 
   def test_user_registration():
       response = client.post("/users", json={
           "email": "test@example.com",
           "name": "Test User",
           "password": "testpass123",
           "confirm-password": "testpass123"
       })
       assert response.status_code == 200
       assert response.json()["email"] == "test@example.com"
```
### Authentication
- Send a POST request to `/token` with valid login credentials.
```python 
   def test_authentication():
       # Login
       response = client.post("/token", data={
           "email": "test@example.com",
           "password": "testpass123"
       })
       assert response.status_code == 200
       assert "access_token" in response.json()
```
- Use the received token in the `Authorization` header for subsequent requests.

### Email Fetching
- After login, send a GET request to `/emails` with the access token.
```python 
   def test_email_fetching():
       response = client.get("/emails", 
           headers={"Authorization": f"Bearer {token}"})
       assert response.status_code == 200
       assert isinstance(response.json(), list)
```
- Use `/emails/{message_id}` for specific email details.
- Use `/emails/{message_id}/attachments/{attachment_id}` to download attachments.

---

## Workflow

### Authentication Flow
1. User registers or logs in.
2. Receives JWT token.
3. Uses token in Authorization header for subsequent API calls.

### Email Processing Flow
1. Authenticated user makes an email request.
2. System connects to Gmail API.
3. Fetches, processes, and returns formatted email data.

### Attachment Handling
1. Authenticated user requests an attachment.
2. System downloads the attachment from Gmail.
3. Returns the file either as a stream or in base64 format.

---

## Gmail API Setup

1. Enable Gmail API from Google Cloud Console.
2. Download `credentials.json`.
3. Place the file in the project root.
4. Run the application to generate `token.pickle` on first use.

---

## Running the Application

```bash
python main.py
```
This will launch the API server and connect to the Gmail API.

```bash
uvicorn main:app --reload
```
Use this command for development with auto-reloading enabled.

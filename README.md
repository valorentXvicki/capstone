# Athletic Spirit - AI Coach Platform

A performance hub for athletes and coaches featuring live event recommendations, a training planner, and an AI-powered chatbot coach.

## Features

- **AI Coach Chatbot**: Get personalized training advice, recommendations, and answers to your fitness questions
- **Event Recommendations**: Find run clubs, races, and sporting events tailored to your interests
- **Training Dashboard**: Track your workload, recovery, and readiness metrics
- **Activity Logging**: Log runs, workouts, and training sessions

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A modern web browser (Chrome, Firefox, Safari, or Edge)

## Quick Start Guide

### Step 1: Install Backend Dependencies

Navigate to the backend directory and install required packages:

```bash
cd backend
pip3 install -r requirements.txt
```

### Step 2: Start the Backend Server

You can start the backend server using either of these methods:

**Option A: Using the startup script**
```bash
./start_backend.sh
```

**Option B: Using uvicorn directly**
```bash
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The backend server will start on `http://127.0.0.1:8000`

You should see output like:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 3: Open the Frontend

Open `athleteai.html` in your web browser. You can do this by:

- Double-clicking the file in your file explorer
- Right-clicking the file and selecting "Open with" > Your preferred browser
- Using a local web server (recommended for development):
  ```bash
  # From the project root directory
  python3 -m http.server 8080
  ```
  Then navigate to `http://localhost:8080/athleteai.html`

### Step 4: Test the AI Coach

1. Scroll down to the "Your AI Coach is Ready" section
2. Click on one of the quick prompt buttons (e.g., "Recommend clubs") or type your own question
3. Click "Send" and wait for the AI coach to respond

## Configuration

### OpenAI API (Optional)

The chatbot uses GPT-2 as a local fallback model by default. To use OpenAI's GPT-3.5-turbo for better responses:

1. Get an API key from [OpenAI](https://platform.openai.com/api-keys)
2. Set the environment variable before starting the backend:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ./start_backend.sh
   ```

If no OpenAI API key is provided, the system will automatically use the local GPT-2 model.

## Troubleshooting

### "Sorry, I'm having trouble connecting to the backend"

This error appears when:
1. The backend server is not running
2. The backend server is running on a different port

**Solution:**
- Make sure the backend server is running on port 8000
- Check the console output for any error messages
- Verify the backend is accessible at `http://127.0.0.1:8000/health`

### Installation Issues

If you encounter issues installing dependencies:

```bash
# Update pip
pip3 install --upgrade pip

# Install dependencies one by one if batch install fails
pip3 install fastapi uvicorn pydantic
pip3 install transformers torch
pip3 install openai tenacity apscheduler
```

### Port Already in Use

If port 8000 is already in use, you can start the server on a different port:

```bash
python3 -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

Then update line 645 in `athleteai.html`:
```javascript
const BACKEND_URL = 'http://127.0.0.1:8001/chat';
```

## Architecture

- **Frontend**: HTML/CSS/JavaScript (athleteai.html)
- **Backend**: FastAPI (Python)
- **AI Models**: 
  - OpenAI GPT-3.5-turbo (optional, requires API key)
  - Local GPT-2 (fallback, no API key required)
- **Recommendation Engine**: BART-based zero-shot classification

## API Endpoints

- `POST /chat` - Send a message to the AI coach
- `GET /health` - Check backend server health
- `GET /metrics` - View performance metrics (if available)
- `/recsys/*` - Event recommendation endpoints

## Project Structure

```
capstone/
├── athleteai.html          # Main frontend page with AI coach
├── dashboard.html          # Training dashboard
├── login.html             # User authentication
├── signup.html            # User registration
├── auth.js                # Authentication logic
├── backend/
│   ├── main.py            # FastAPI server and chatbot logic
│   ├── recsys.py          # Recommendation system
│   ├── event_fetcher.py   # Event scraping utilities
│   ├── requirements.txt   # Python dependencies
│   └── start_backend.sh   # Backend startup script
└── README.md              # This file
```

## Development

To run in development mode with auto-reload:

```bash
cd backend
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## Support

For issues or questions, contact: athleticspirit@gmail.com

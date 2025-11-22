from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
try:
    from .recsys import router
except ImportError:
    from recsys import router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio

app = FastAPI(title="Chatbot Backend", description="Hybrid AI Chatbot with Generative and Deterministic Components")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Note: GPT-2 model removed to avoid internet dependency at startup
# Using simple fallback responses instead

# OpenAI API key from environment variable (used in call_openai function)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)

# Simple dialogue state (in-memory; use Redis for production)
conversation_states = {}  # user_id: {"state": "initial", "context": {}}

class ChatRequest(BaseModel):
    user_input: str
    user_id: str = "default"  # For session tracking

@app.post("/chat")
async def chat(request: ChatRequest):
    user_input = request.user_input.lower()
    user_id = request.user_id

    # Initialize or retrieve state
    if user_id not in conversation_states:
        # The history will start with the system prompt
        conversation_states[user_id] = {"context": {"history": [{"role": "system", "content": "You are a helpful AI assistant."}]}}
    state = conversation_states[user_id]

    # Add user's current input to the history
    state["context"]["history"].append({"role": "user", "content": request.user_input})

    # Try OpenAI first if API key is available
    response = None
    if OPENAI_API_KEY:
        try:
            @retry( # Error handling and retries are already properly implemented with tenacity
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=2, min=2, max=30),
                retry=retry_if_exception_type(openai.RateLimitError)
            )
            def call_openai():
                client = openai.OpenAI(api_key=OPENAI_API_KEY)
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=state["context"]["history"], # Use the full conversation history
                    max_tokens=300,  # Increased for longer responses
                    temperature=0.7
                )
                return completion.choices[0].message.content.strip()

            response = call_openai()
        except Exception as e:
            print(f"OpenAI error: {e}")
            response = None
    
    # Fallback response if OpenAI is not available
    if response is None:
        # Provide helpful responses based on common queries
        user_input_lower = request.user_input.lower()
        
        if any(word in user_input_lower for word in ['hello', 'hi', 'hey', 'greet']):
            response = "Hello! I'm your AI Coach. I can help you with training advice, event recommendations, and fitness questions. What would you like to know today?"
        elif any(word in user_input_lower for word in ['train', 'workout', 'exercise']):
            response = "For training advice, I recommend starting with a structured plan that includes rest days. What's your current fitness level and training goal?"
        elif any(word in user_input_lower for word in ['event', 'race', 'club', 'run']):
            response = "Check out the recommended events and run clubs section above! I can help you find events that match your interests and schedule."
        elif any(word in user_input_lower for word in ['help', 'what can you do']):
            response = "I can help you with:\n• Training advice and workout planning\n• Finding local run clubs and events\n• Logging your activities\n• Recovery and nutrition tips\n\nWhat would you like to explore?"
        else:
            response = f"I understand you're asking about: '{request.user_input}'. As your AI coach, I'm here to help with training, events, and fitness guidance. Could you provide more details about what you'd like to know?"

    # Add AI's response to the history to maintain context for the next turn
    state["context"]["history"].append({"role": "assistant", "content": response})

    return {
        "response": response
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/metrics")
async def get_metrics():
    try:
        return FileResponse("chatbot_project/performance_metrics.png", media_type="image/png")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Metrics image not found. Please train the model first.")

# Include recsys router
app.include_router(router, prefix="/recsys", tags=["recommendation"])

# Predefined sources for automatic scraping
PREDEFINED_SOURCES = [
    "https://www.playo.co/events",  # Example sports event site
    "https://www.meetup.com/cities/us/ny/sports-outdoors/",  # Example meetup for sports
    # Add more sources as needed
]

# Scheduler for automatic updates
scheduler = AsyncIOScheduler()

async def auto_update_events():
    """Automatically scrape and update events from predefined sources."""
    print("Starting automatic event update...")
    for url in PREDEFINED_SOURCES:
        try:
            # Scrape events
            events = scraper.scrape_sports_events(url)
            events_db.extend(events)
            print(f"Scraped {len(events)} events from {url}")
        except Exception as e:
            print(f"Error scraping {url}: {e}")
    # Update events with AI
    try:
        updated_events = []
        for event in events_db:
            updated = updater.update_event_with_ai(event)
            updated_events.append(updated)
        events_db[:] = updated_events
        print("Events updated with AI")
    except Exception as e:
        print(f"Error updating events: {e}")

# Add job to scheduler
scheduler.add_job(auto_update_events, trigger=IntervalTrigger(hours=1), id="auto_update")

@app.on_event("startup")
async def startup_event():
    scheduler.start()
    print("Scheduler started. Events will be updated hourly.")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("Scheduler shut down.")

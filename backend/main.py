from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline
import openai
import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .recsys import router, gen_model as recsys_gen_model
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

gen_model = pipeline("text-generation", model="gpt2", max_length=150, do_sample=True, temperature=0.7)  # Local generative AI with better parameters

# Set gen_model for recsys
recsys_gen_model = gen_model

# OpenAI API key (set as environment variable or replace with your key)
openai.api_key = os.getenv("OPENAI_API_KEY", "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")

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

    try:
        @retry( # Error handling and retries are already properly implemented with tenacity
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=2, min=4, max=60),
            retry=retry_if_exception_type(openai.RateLimitError)
        )
        def call_openai():
            client = openai.OpenAI(api_key=openai.api_key)
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
        # Fallback to local GPT-2 if OpenAI fails
        try:
            prompt = f"You are a helpful AI assistant. Respond to: '{request.user_input}'."
            generated = gen_model(prompt, max_length=150, do_sample=True, temperature=0.7)
            response = generated[0]['generated_text'].replace(prompt, '').strip()
            if not response:
                response = "I'm sorry, I'm having trouble generating a response right now. Please try again."
        except Exception as e2:
            print(f"GPT-2 error: {e2}")
            response = "I'm sorry, I'm currently unable to process your request. Please try again later."

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

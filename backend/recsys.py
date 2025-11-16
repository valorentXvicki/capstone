from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Reuse AI from main.py (will be passed or imported)
gen_model = None  # To be set from main.py

router = APIRouter()

# In-memory storage for events
events_db: List[Dict] = []

class Event(BaseModel):
    name: str
    date: str
    location: str
    description: str
    link: str
    category: str = "sports"  # Default category

class Scraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def scrape_sports_events(self, url: str) -> List[Dict]:
        """Scrape sports events from a given URL."""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            events = []
            # Example: Assume events are in divs with class 'event'
            for event_div in soup.find_all('div', class_='event'):
                name = event_div.find('h2').text.strip() if event_div.find('h2') else "Unknown"
                date = event_div.find('span', class_='date').text.strip() if event_div.find('span', class_='date') else "TBD"
                location = event_div.find('span', class_='location').text.strip() if event_div.find('span', class_='location') else "Unknown"
                description = event_div.find('p', class_='desc').text.strip() if event_div.find('p', class_='desc') else "No description"
                link = event_div.find('a')['href'] if event_div.find('a') else url
                events.append({
                    "name": name,
                    "date": date,
                    "location": location,
                    "description": description,
                    "link": link,
                    "category": "sports"
                })
            return events
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

class EventUpdater:
    def __init__(self, gen_model, gemini_key):
        self.gen_model = gen_model
        self.gemini_key = gemini_key
        genai.configure(api_key=self.gemini_key)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')

    def update_event_with_ai(self, event: Dict) -> Dict:
        """Use Gemini to enhance event description."""
        try:
            prompt = f"Enhance this sports event description with more details, category, and appeal: {event['description']}"
            response = self.gemini_model.generate_content(prompt)
            event['description'] = response.text.strip()
            return event
        except Exception as e:
            print(f"Gemini error: {e}")
            # Fallback to local GPT-2 if Gemini fails
            try:
                prompt = f"You are a helpful AI assistant. Enhance this sports event description: '{event['description']}'."
                generated = self.gen_model(prompt, max_length=150, do_sample=True, temperature=0.7)
                response = generated[0]['generated_text'].replace(prompt, '').strip()
                event['description'] = response
                return event
            except:
                return event  # Return unchanged if AI fails

class Recommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')

    def recommend(self, user_preferences: str, events: List[Dict], top_n: int = 5) -> List[Dict]:
        """Recommend events based on user preferences using content similarity."""
        if not events:
            return []
        descriptions = [event['description'] for event in events]
        tfidf_matrix = self.vectorizer.fit_transform(descriptions + [user_preferences])
        similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1]).flatten()
        top_indices = similarities.argsort()[-top_n:][::-1]
        return [events[i] for i in top_indices]

scraper = Scraper()
updater = EventUpdater(gen_model, os.getenv("GEMINI_API_KEY"))
recommender = Recommender()

@router.post("/scrape-events")
async def scrape_events(url: str):
    """Scrape events from web."""
    events = scraper.scrape_sports_events(url)
    events_db.extend(events)
    return {"message": f"Scraped {len(events)} events", "events": events}

@router.post("/update-events")
async def update_events():
    """Update all events with AI."""
    updated_events = []
    for event in events_db:
        updated = updater.update_event_with_ai(event)
        updated_events.append(updated)
    events_db[:] = updated_events  # Update in place
    return {"message": "Events updated with AI", "events": events_db}

@router.get("/recommend-events")
async def recommend_events(user_preferences: str, top_n: int = 5):
    """Get event recommendations based on user preferences."""
    recommendations = recommender.recommend(user_preferences, events_db, top_n)
    return {"recommendations": recommendations}

@router.get("/get-event-link")
async def get_event_link(event_name: str):
    """Get enrollment link for a specific event."""
    for event in events_db:
        if event['name'].lower() == event_name.lower():
            return {"link": event['link']}
    raise HTTPException(status_code=404, detail="Event not found")

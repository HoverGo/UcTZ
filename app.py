import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

# CONST
DATABASE_URL = 'reviews.db'
POSITIVE_WORDS = {'хорош', 'люблю'}
NEGATIVE_WORDS = {'плох', 'ненавиж'}

# PYDANTIC MODELS
class ReviewCreate(BaseModel):
    text: str

class ReviewResponse(BaseModel):
    id: int
    text: str
    sentiment: str
    created_at: str

# DATABASE MANAGER
class Database:

    def __init__(self, db_url: str = DATABASE_URL):
        self.db_url = db_url
        self.init_db()

    @contextmanager
    def get_conn(self):
        conn = sqlite3.connect(self.db_url)
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    sentiment TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            conn.commit()


# SENTIMENTS
def analyze_sentiment(review: str) -> str:
    review_lower = review.lower()

    if any(word in review_lower for word in POSITIVE_WORDS):
        return "positive"
    elif any(word in review_lower for word in NEGATIVE_WORDS):
        return "negative"
    return "neutral"

# INIT
db = Database()
app = FastAPI()


# ENDPOINTS
@app.post("/reviews", response_model=ReviewResponse)
def create_review(review: ReviewCreate):
    sentiment = analyze_sentiment(review.text)
    created_at = datetime.utcnow().isoformat()

    with db.get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            
            "INSERT INTO reviews (text, sentiment, created_at) VALUES (?, ?, ?)",
            (review.text, sentiment, created_at)
        )
        review_id = cursor.lastrowid
        conn.commit()
        
        return {
            "id": review_id,
            "text": review.text,
            "sentiment": sentiment,
            "created_at": created_at
        }
    

@app.get("/reviews", response_model=List[ReviewResponse])
def get_reviews(sentiment: Optional[str] = None):
    with db.get_conn() as conn:
        cursor = conn.cursor()

        if sentiment:
            cursor.execute(
                "SELECT id, text, sentiment, created_at FROM reviews WHERE sentiment = ?",
                (sentiment.lower(),)
            )
        else:
            cursor.execute(
                "SELECT id, text, sentiment, created_at FROM reviews"
            )
        reviews = cursor.fetchall()
        
        return [
            {
                "id": row[0],
                "text": row[1],
                "sentiment": row[2],
                "created_at": row[3]
            }
            for row in reviews
        ]
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
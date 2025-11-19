import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import create_document, get_documents, db
from schemas import Lead

app = FastAPI(title="Luxury Real Estate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Luxury Real Estate Backend Running"}

# Public: list projects (static for now, could come from DB later)
class Project(BaseModel):
    id: str
    title: str
    location: str
    hero_video: Optional[str] = None
    thumbnail: Optional[str] = None
    status: str
    description: str
    available_units: int
    virtual_tour_url: Optional[str] = None

# Seed sample projects (in-memory constants; real data can be moved to DB later)
SAMPLE_PROJECTS: List[Project] = [
    Project(
        id="aurora-towers",
        title="Aurora Towers",
        location="Downtown",
        status="Now Selling",
        description="Ultra-modern residences with panoramic skyline views.",
        available_units=21,
        hero_video="https://cdn.coverr.co/videos/coverr-city-sunrise-1300/1080p.mp4",
        virtual_tour_url="https://www.youtube.com/embed/Scxs7L0vhZ4",
        thumbnail="https://images.unsplash.com/photo-1501183638710-841dd1904471?q=80&w=1600&auto=format&fit=crop"
    ),
    Project(
        id="serenity-bay",
        title="Serenity Bay",
        location="Waterfront",
        status="Under Construction",
        description="Private marina residences with resort amenities.",
        available_units=8,
        hero_video="https://cdn.coverr.co/videos/coverr-sunrise-over-the-sea-4210/1080p.mp4",
        virtual_tour_url="https://www.youtube.com/embed/ysz5S6PUM-U",
        thumbnail="https://images.unsplash.com/photo-1494526585095-c41746248156?q=80&w=1600&auto=format&fit=crop"
    ),
]

@app.get("/api/projects", response_model=List[Project])
def get_projects():
    return SAMPLE_PROJECTS

@app.get("/api/projects/{project_id}", response_model=Project)
def get_project(project_id: str):
    for p in SAMPLE_PROJECTS:
        if p.id == project_id:
            return p
    raise HTTPException(status_code=404, detail="Project not found")

# Leads endpoints (persist to MongoDB)
@app.post("/api/leads")
def create_lead(lead: Lead):
    try:
        inserted_id = create_document("lead", lead)
        return {"status": "ok", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leads")
def list_leads(limit: int = 50):
    try:
        docs = get_documents("lead", limit=limit)
        # Convert ObjectId to string for JSON
        for d in docs:
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

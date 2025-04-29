from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from pydantic import BaseModel
from uuid import UUID
from typing import Optional

from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

pool = None

# Database pool
async def create_db_pool():
    global pool
    pool = await asyncpg.create_pool(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        ssl="require"
    )

async def close_db_pool():
    await pool.close()

@app.on_event("startup")
async def startup():
    await create_db_pool()

@app.on_event("shutdown")
async def shutdown():
    await close_db_pool()

# Request model
class TemplateData(BaseModel):
    name: str
    type: str
    locate_narrative: str
    work_prints: str
    project_gid: UUID

    note_distance_from_start_intersection: Optional[bool] = False
    note_distance_from_end_intersection: Optional[bool] = False
    note_address_at_start: Optional[bool] = False
    note_address_at_end: Optional[bool] = False
    include_gps_at_start: Optional[bool] = False
    include_gps_at_end: Optional[bool] = False
    include_gps_at_bearing: Optional[bool] = False
# Save template
@app.post("/saveTemplate")
async def saveTemplate(data: TemplateData):
    try:
        async with pool.acquire() as conn:
            query = """
                INSERT INTO archive.line_locates (
                    name, type, locate_narrative, work_prints, project_gid,
                    note_distance_from_start_intersection,
                    note_distance_from_end_intersection,
                    note_address_at_start,
                    note_address_at_end,
                    include_gps_at_start,
                    include_gps_at_end,
                    include_gps_at_bearing
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING pk
            """
            result = await conn.fetchrow(
                query,
                data.name,
                data.type,
                data.locate_narrative,
                data.work_prints,
                str(data.project_gid),
                data.note_distance_from_start_intersection,
                data.note_distance_from_end_intersection,
                data.note_address_at_start,
                data.note_address_at_end,
                data.include_gps_at_start,
                data.include_gps_at_end,
                data.include_gps_at_bearing,
            )
            if result:
                return {"message": "Template saved successfully", "pk": result["pk"]}
            else:
                raise HTTPException(status_code=500, detail="Failed to save template")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Get all templates
@app.get("/getTemplates")
async def getTemplates():
    try:
        async with pool.acquire() as conn:
            query = """
                SELECT pk, name, type, locate_narrative, work_prints, project_gid,
                       note_distance_from_start_intersection,
                       note_distance_from_end_intersection,
                       note_address_at_start, note_address_at_end,
                       include_gps_at_start, include_gps_at_end, include_gps_at_bearing
                FROM archive.line_locates
            """
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
        print("Connecting to DB:", DB_HOST, DB_NAME)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")

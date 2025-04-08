from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from pydantic import BaseModel
import uuid

app = FastAPI()

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB Config
DB_HOST = "dpg-cu88cibv2p9s73c8pj1g-a.ohio-postgres.render.com"
DB_NAME = "prod_narrative"
DB_USER = "ces_admin_narrative"
DB_PASSWORD = "Do9oO6I9NlAiPXRlGHRdD9XhG9yz1LQQ"
DB_PORT = 5432

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
    project_gid: uuid.UUID
    toggles: dict 

# Save template
@app.post("/saveTemplate")
async def save_template(data: TemplateData):
    try:
        t = data.toggles

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
                ) VALUES (
                    $1, $2, $3, $4, $5,
                    $6, $7, $8, $9, $10, $11, $12
                ) RETURNING pk;
            """

            result = await conn.fetchrow(
                query,
                data.name,
                data.type,
                data.locate_narrative,
                data.work_prints,
                data.project_gid,
                t.get("note_distance_from_start_intersection", False),
                t.get("note_distance_from_end_intersection", False),
                t.get("note_address_at_start", False),
                t.get("note_address_at_end", False),
                t.get("include_gps_at_start", False),
                t.get("include_gps_at_end", False),
                t.get("include_gps_at_bearing", False)
            )

            return {"message": "Template saved successfully", "pk": result["pk"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Get all templates
@app.get("/get_templates")
async def get_templates():
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")

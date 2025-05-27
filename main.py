from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Union
import os
import uvicorn
import asyncpg


# ...

app = FastAPI()

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pool = None

@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 5432)),
        min_size=1,
        max_size=5
    )


# Incoming payload structure
class SubmitTemplatePayload(BaseModel):
    name: str
    type: str
    locate_narrative: str
    work_prints: str
    max_length : int
    project_gid: UUID
    note_distance_from_start_intersection: Optional[bool] = False
    note_distance_from_end_intersection: Optional[bool] = False
    note_address_at_start: Optional[bool] = False
    note_address_at_end: Optional[bool] = False
    include_gps_at_start: Optional[bool] = False
    include_gps_at_end: Optional[bool] = False
    include_gps_at_bearing: Optional[bool] = False

class IncomingRequest(BaseModel):
    function: str
    payload: Union[dict, None]

# Unified API
@app.post("/api")
async def unified_handler(request: IncomingRequest):
    if request.function == "submit_template":
        return await handle_submit_template(SubmitTemplatePayload(**request.payload))
    elif request.function == "get_templates":
        return await handle_get_templates()
    else:
        raise HTTPException(status_code=400, detail="Unknown function name")


async def handle_submit_template(data: SubmitTemplatePayload):
    try:
        async with pool.acquire() as conn:
            query = """
                INSERT INTO archive.line_locates (
                    name, type, locate_narrative, work_prints, max_narrative_length, project_gid,
                    note_distance_from_start_intersection,
                    note_distance_from_end_intersection,
                    note_address_at_start,
                    note_address_at_end,
                    include_gps_at_start,
                    include_gps_at_end,
                    include_gps_at_bearing
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING pk
            """
            result = await conn.fetchrow(
                query,
                data.name,
                data.type,
                data.locate_narrative,
                data.work_prints,
                data.max_length,  # mapped to max_narrative_length in DB
                str(data.project_gid),
                data.note_distance_from_start_intersection,
                data.note_distance_from_end_intersection,
                data.note_address_at_start,
                data.note_address_at_end,
                data.include_gps_at_start,
                data.include_gps_at_end,
                data.include_gps_at_bearing,
            )
            return {"message": "Template saved successfully", "pk": result["pk"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
# Get templates
async def handle_get_templates():
    try:
        async with pool.acquire() as conn:
            query = """
                        SELECT pk, name, type, locate_narrative, work_prints, max_narrative_length AS max_length, project_gid,
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
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

@app.get("/")
def root():
    return {"message": "API is running. Use POST /api to interact."}
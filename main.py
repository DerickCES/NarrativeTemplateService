from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
import os

app = FastAPI()

# Enable CORS to allow your React frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL for better security
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Database credentials
DB_HOST = "dpg-cu88cibv2p9s73c8pj1g-a.ohio-postgres.render.com"
DB_NAME = "prod_narrative"
DB_USER = "ces_admin_narrative"
DB_PASSWORD = "Do9oO6I9NlAiPXRlGHRdD9XhG9yz1LQQ"
DB_PORT = 5432

# Connection pool (will be initialized on startup)
pool = None

# Function to create a database connection pool
async def create_db_pool():
    global pool
    pool = await asyncpg.create_pool(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        ssl="require"  # Required for Render-hosted databases
    )

# Close the connection pool on shutdown
async def close_db_pool():
    await pool.close()

# Initialize the database connection pool when the app starts
@app.on_event("startup")
async def startup():
    await create_db_pool()

# Close the database pool when the app shuts down
@app.on_event("shutdown")
async def shutdown():
    await close_db_pool()

# Fetch data from the database
@app.get("/_save_template")
async def fetch_data(type: str = Query(..., description="Specify 'Poles' or 'Connections'"), status: str = None):
    try:
        if not pool:
            raise HTTPException(status_code=500, detail="Database connection not initialized.")

        query = ""
        if type == "Poles":
            query = "SELECT pk, name, type, pole_use, ST_AsText(geom) as geom FROM sales.poles"
        elif type == "Connections":
            if status:
                query = """
                    SELECT pk, pole_name, frogfoot_free,strength_active, active, dormant, ina, ST_AsText(geom) as geom 
                    FROM sales.connections022025 
                    WHERE {status} = true
                """
            else:
                query = """
                    SELECT pk, pole_name, frogfoot_free,strength_active, active, dormant, ina, ST_AsText(geom) as geom 
                    FROM sales.connections022025
                """
        else:
            raise HTTPException(status_code=400, detail="Invalid type parameter. Use 'Poles' or 'Connections'.")

        async with pool.acquire() as connection:
            rows = await connection.fetch(query)

        return [dict(row) for row in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")

# Run the app (Only needed for local testing, not required on Render)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)

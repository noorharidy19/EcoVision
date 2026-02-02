from fastapi import FastAPI
import os
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine
from app.models import User
from app.core.database import Base
from app.api.routes import users
from app.api.routes import projects
from app.api.routes import auth
from app.api.routes import files_protected
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from app.core.database import engine
from app.models import User
from app.core.database import Base
from app.api.routes import users
from app.api.routes import projects
from app.api.routes import auth
from fastapi.staticfiles import StaticFiles
from app.api.routes import admin
from app.api.routes import floorplan
from app.api.routes import analysis as analysis_router




app = FastAPI(title="ECoVision API")
app.mount("/files", StaticFiles(directory="uploaded_files"), name="files")

# Enable CORS for development (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(auth.router)
app.include_router(files_protected.router)
app.include_router(admin.router)
app.include_router(floorplan.router)
app.include_router(analysis_router.router)


# If RESET_DB is set to a truthy value, drop and recreate all tables.
# WARNING: this will DELETE DATA. Use only in development or after backup.



@app.get("/")
def root():
    return {"message": "ECoVision backend is running"}

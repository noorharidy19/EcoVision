from fastapi import FastAPI
from app.core.database import engine
from app.models import User
from app.core.database import Base
from app.api.routes import users
from app.api.routes import projects
from fastapi.staticfiles import StaticFiles



app = FastAPI(title="ECoVision API")
app.mount("/files", StaticFiles(directory="uploaded_files"), name="files")

app.include_router(users.router)
app.include_router(projects.router)



Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "ECoVision backend is running"}

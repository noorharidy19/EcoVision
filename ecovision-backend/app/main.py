from fastapi import FastAPI
from app.core.database import engine
from app.models import User
from app.core.database import Base
from app.api.routes import users


app = FastAPI(title="ECoVision API")
app.include_router(users.router)


Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "ECoVision backend is running"}

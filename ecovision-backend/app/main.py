from fastapi import FastAPI

app = FastAPI(title="ECoVision API")

@app.get("/")
def root():
    return {"message": "ECoVision backend is running"}

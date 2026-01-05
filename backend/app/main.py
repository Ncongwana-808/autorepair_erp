from fastapi import FastAPI
from database import get_db
from models import CustomerCreate
from queries import create_customer



app = FastAPI(title="Auto Rpair Workshop Management System")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Auto Rpair Workshop Management System API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


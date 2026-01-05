from fastapi import FastAPI
from app.database import get_db, close_db_connection
from app.models import CustomerCreate
from app.queries import create_customer

app = FastAPI(title="Auto Rpair Workshop Management System")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Auto Rpair Workshop Management System API"}


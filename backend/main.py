
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Transaction

from csv_importer import router as csv_import_router
from analytics import router as analytics_router
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create missing tables for this initial prototype.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SpendSense API",
    description="Personal expense intelligence system",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(csv_import_router)
app.include_router(analytics_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TransactionCreate(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category: str = Field(default="Uncategorized", max_length=100)
    transaction_date: date
    transaction_type: Literal["expense", "income"] = "expense"
    notes: str | None = None


class TransactionResponse(TransactionCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


@app.get("/")
def home():
    return {
        "message": "Welcome to SpendSense",
        "status": "running",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SpendSense API",
    }


@app.get("/api/db-health")
def database_health(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
        return {"status": "connected", "database": "spendsense_db"}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed. Check server logs.",
        ) from exc


@app.post(
    "/api/transactions",
    response_model=TransactionResponse,
    status_code=201,
)
def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
):
    transaction = Transaction(**transaction_data.model_dump())

    db.add(transaction)

    try:
        db.commit()
        db.refresh(transaction)
        return transaction
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not save transaction.",
        )


@app.get(
    "/api/transactions",
    response_model=list[TransactionResponse],
)
def list_transactions(db: Session = Depends(get_db)):
    statement = select(Transaction).order_by(
        Transaction.transaction_date.desc(),
        Transaction.id.desc(),
    )
    return list(db.scalars(statement).all())

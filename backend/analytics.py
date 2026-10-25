
from calendar import monthrange
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from models import Transaction


router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def get_month_range(year: int, month: int):
    """Return the inclusive start and exclusive end dates for a month."""

    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400,
            detail="Month must be between 1 and 12.",
        )

    start = date(year, month, 1)

    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    return start, end


def money(value):
    """Convert database Decimal values into JSON-friendly numbers."""
    return float(value or Decimal("0.00"))


@router.get("/summary")
def monthly_summary(
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
):
    start, end = get_month_range(year, month)

    statement = select(
        func.coalesce(
            func.sum(Transaction.amount).filter(
                Transaction.transaction_type == "income"
            ),
            0,
        ).label("income"),
        func.coalesce(
            func.sum(Transaction.amount).filter(
                Transaction.transaction_type == "expense"
            ),
            0,
        ).label("expenses"),
        func.count(Transaction.id).label("transaction_count"),
    ).where(
        Transaction.transaction_date >= start,
        Transaction.transaction_date < end,
    )

    result = db.execute(statement).one()

    income = money(result.income)
    expenses = money(result.expenses)

    return {
        "year": year,
        "month": month,
        "total_income": income,
        "total_expenses": expenses,
        "balance": round(income - expenses, 2),
        "transaction_count": result.transaction_count,
    }


@router.get("/categories")
def category_breakdown(
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
):
    start, end = get_month_range(year, month)

    statement = (
        select(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .where(
            Transaction.transaction_date >= start,
            Transaction.transaction_date < end,
            Transaction.transaction_type == "expense",
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
    )

    rows = db.execute(statement).all()

    total_expenses = sum(
        (row.total for row in rows),
        Decimal("0.00"),
    )

    return {
        "year": year,
        "month": month,
        "total_expenses": money(total_expenses),
        "categories": [
            {
                "category": row.category,
                "amount": money(row.total),
                "transaction_count": row.count,
                "percentage": round(
                    float(row.total / total_expenses * 100), 2
                ) if total_expenses else 0,
            }
            for row in rows
        ],
    }


@router.get("/monthly-trends")
def monthly_trends(
    months: int = Query(default=6, ge=1, le=24),
    db: Session = Depends(get_db),
):
    """Return the last N calendar months, including months with no data."""

    today = date.today()

    # First day of the current month.
    current_month = date(today.year, today.month, 1)

    # Find the first month in the requested range.
    month_index = (
        current_month.year * 12 + current_month.month - 1
    ) - (months - 1)

    start_year, start_month_index = divmod(month_index, 12)
    start = date(start_year, start_month_index + 1, 1)

    statement = (
        select(
            func.date_trunc(
                "month", Transaction.transaction_date
            ).label("month_start"),
            func.coalesce(
                func.sum(Transaction.amount).filter(
                    Transaction.transaction_type == "income"
                ),
                0,
            ).label("income"),
            func.coalesce(
                func.sum(Transaction.amount).filter(
                    Transaction.transaction_type == "expense"
                ),
                0,
            ).label("expenses"),
        )
        .where(Transaction.transaction_date >= start)
        .group_by("month_start")
        .order_by("month_start")
    )

    rows = db.execute(statement).all()

    results = {
        row.month_start.date(): {
            "income": money(row.income),
            "expenses": money(row.expenses),
        }
        for row in rows
    }

    trends = []

    for offset in range(months):
        index = month_index + offset
        year, month_index_part = divmod(index, 12)
        month_start = date(year, month_index_part + 1, 1)

        values = results.get(
            month_start,
            {"income": 0.0, "expenses": 0.0},
        )

        trends.append({
            "month": month_start.strftime("%Y-%m"),
            "income": values["income"],
            "expenses": values["expenses"],
            "balance": round(
                values["income"] - values["expenses"], 2
            ),
        })

    return {"months": trends}


@router.get("/recent-transactions")
def recent_transactions(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    statement = (
        select(Transaction)
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .limit(limit)
    )

    transactions = db.scalars(statement).all()

    return {
        "count": len(transactions),
        "transactions": [
            {
                "id": transaction.id,
                "description": transaction.description,
                "amount": money(transaction.amount),
                "category": transaction.category,
                "transaction_date": (
                    transaction.transaction_date.isoformat()
                ),
                "transaction_type": transaction.transaction_type,
            }
            for transaction in transactions
        ],
    }

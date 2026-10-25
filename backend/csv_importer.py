
import csv
import hashlib
import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from categorizer import categorize_transaction
from database import get_db
from models import ImportBatch, Transaction


router = APIRouter(prefix="/api", tags=["CSV Import"])

MAX_FILE_SIZE = 5 * 1024 * 1024

ALIASES = {
    "date": ["date", "transaction_date"],
    "description": ["description", "details", "narration"],
    "amount": ["amount"],
    "type": ["type", "transaction_type"],
}


def parse_date(value: str) -> date:
    value = value.strip()

    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    raise ValueError("Invalid date. Use YYYY-MM-DD or DD/MM/YYYY.")


def parse_amount(value: str) -> Decimal:
    cleaned = value.strip().replace(",", "").replace("₹", "").strip()

    try:
        amount = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError("Amount must be a valid number.") from exc

    if not amount.is_finite() or amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    if amount.as_tuple().exponent < -2:
        raise ValueError("Amount cannot have more than 2 decimal places.")

    if amount >= Decimal("10000000000"):
        raise ValueError("Amount is too large.")

    return amount


def get_column_mapping(headers: list[str]) -> dict[str, str]:
    normalized = {
        header.strip().lower(): header
        for header in headers
        if header
    }

    mapping = {}

    for field, aliases in ALIASES.items():
        matched = next(
            (normalized[a] for a in aliases if a in normalized),
            None,
        )

        if matched is None:
            raise ValueError(
                f"Missing required column: {field}. "
                f"Accepted names: {', '.join(aliases)}"
            )

        mapping[field] = matched

    return mapping


@router.post("/transactions/import")
async def import_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a .csv file.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="CSV file must be 5 MB or smaller.",
        )

    if not content:
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    file_hash = hashlib.sha256(content).hexdigest()

    previous = db.scalar(
        select(ImportBatch).where(ImportBatch.file_hash == file_hash)
    )

    if previous:
        raise HTTPException(
            status_code=409,
            detail="This exact CSV file has already been imported.",
        )

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="CSV must use UTF-8 encoding.",
        ) from exc

    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV has no header row.")

    try:
        mapping = get_column_mapping(reader.fieldnames)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    imported = 0
    rejected = []
    seen_rows = set()
    transactions = []

    for row_number, row in enumerate(reader, start=2):
        try:
            if None in row:
                raise ValueError("Too many columns in this row.")

            description = (row.get(mapping["description"]) or "").strip()
            if not description or len(description) > 200:
                raise ValueError("Description must contain 1–200 characters.")

            transaction_date = parse_date(
                row.get(mapping["date"]) or ""
            )

            amount = parse_amount(row.get(mapping["amount"]) or "")

            transaction_type = (
                (row.get(mapping["type"]) or "").strip().lower()
            )

            if transaction_type not in ("expense", "income"):
                raise ValueError("Type must be 'expense' or 'income'.")

            # Avoid repeated identical rows within this file.
            duplicate_key = (
                transaction_date,
                description.casefold(),
                amount,
                transaction_type,
            )

            if duplicate_key in seen_rows:
                rejected.append({
                    "row": row_number,
                    "reason": "Duplicate transaction within this CSV.",
                })
                continue

            seen_rows.add(duplicate_key)

            category = categorize_transaction(
                description,
                transaction_type,
            )

            transactions.append(
                Transaction(
                    description=description,
                    amount=amount,
                    category=category,
                    transaction_date=transaction_date,
                    transaction_type=transaction_type,
                )
            )

        except ValueError as exc:
            rejected.append({
                "row": row_number,
                "reason": str(exc),
            })

    if not transactions:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "No valid transactions found.",
                "rejected": rejected,
            },
        )

    batch = ImportBatch(
        file_hash=file_hash,
        filename=file.filename[:255],
        imported_count=len(transactions),
    )

    try:
        db.add(batch)
        db.add_all(transactions)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Import failed. No transactions were saved.",
        ) from exc

    imported = len(transactions)

    return {
        "message": "CSV import completed.",
        "filename": file.filename,
        "imported": imported,
        "rejected_count": len(rejected),
        "rejected_rows": rejected,
    }

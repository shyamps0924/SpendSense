
from datetime import date
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import DateTime

from sqlalchemy import (
    Date,
    Integer,
    Numeric,
    String,
    Text,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="check_transaction_amount_positive",
        ),
        CheckConstraint(
            "transaction_type IN ('expense', 'income')",
            name="check_transaction_type",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Uncategorized",
    )

    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="expense",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    file_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    imported_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

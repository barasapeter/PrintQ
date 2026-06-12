import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, MetaData, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=naming_convention)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class JsonMixin:
    properties: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )


class Vendor(Base, TimestampMixin, JsonMixin): 
    __tablename__ = "vendor"

    uuid: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    email_address: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    shops: Mapped[list["Shop"]] = relationship("Shop", back_populates="vendor")

    __table_args__ = (
        Index("ix_vendor_username", "username"),
        Index("ix_vendor_email_address", "email_address"),
    )

    def __repr__(self) -> str:
        return f"<Vendor uuid={self.uuid!s} username={self.username!r}>"


class Customer(Base, TimestampMixin, JsonMixin):
    __tablename__ = "customer"

    uuid: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_uuid.uuid4,
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    print_jobs: Mapped[list["PrintJob"]] = relationship(
        "PrintJob", back_populates="customer"
    )

    def __repr__(self) -> str:
        return f"<Customer uuid={self.uuid!s} name={self.name!r}>"


class Shop(Base, TimestampMixin, JsonMixin):
    __tablename__ = "shop"

    uuid: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_uuid.uuid4,
    )
    vendor_uuid: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendor.uuid", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_contact: Mapped[str | None] = mapped_column(String(30), nullable=True)

    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="shops")
    print_jobs: Mapped[list["PrintJob"]] = relationship(
        "PrintJob", back_populates="shop"
    )
    merchant_ledger_entries: Mapped[list["MerchantLedger"]] = relationship(
        "MerchantLedger", back_populates="shop"
    )

    __table_args__ = (
        Index("ix_shop_vendor_uuid", "vendor_uuid"),
        Index("ix_shop_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<Shop uuid={self.uuid!s} name={self.name!r} vendor_uuid={self.vendor_uuid!s}>"


class PrintJob(Base, TimestampMixin, JsonMixin):
    __tablename__ = "print_jobs"

    uuid: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_uuid.uuid4,
    )
    customer_uuid: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer.uuid", ondelete="CASCADE"),
        nullable=False,
    )
    shop_uuid: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shop.uuid", ondelete="CASCADE"),
        nullable=False,
    )
    checkout_request_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    merchant_request_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result_desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="print_jobs")
    shop: Mapped["Shop"] = relationship("Shop", back_populates="print_jobs")

    __table_args__ = (
        Index("ix_print_jobs_customer_uuid", "customer_uuid"),
        Index("ix_print_jobs_shop_uuid", "shop_uuid"),
        Index("ix_print_jobs_checkout_request_id", "checkout_request_id"),
        Index("ix_print_jobs_merchant_request_id", "merchant_request_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<PrintJob uuid={self.uuid!s} "
            f"shop_uuid={self.shop_uuid!s} "
            f"customer_uuid={self.customer_uuid!s} "
            f"amount={self.amount}>"
        )


class MerchantLedger(Base, TimestampMixin, JsonMixin):
    __tablename__ = "merchant_ledger"

    uuid: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_uuid.uuid4,
    )
    shop_uuid: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shop.uuid", ondelete="CASCADE"),
        nullable=False,
    )
    debit: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    credit: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    desc: Mapped[str | None] = mapped_column(Text, nullable=True)

    shop: Mapped["Shop"] = relationship(
        "Shop", back_populates="merchant_ledger_entries"
    )

    __table_args__ = (Index("ix_merchant_ledger_shop_uuid", "shop_uuid"),)

    def __repr__(self) -> str:
        return (
            f"<MerchantLedger uuid={self.uuid!s} "
            f"shop_uuid={self.shop_uuid!s} "
            f"debit={self.debit} credit={self.credit}>"
        )

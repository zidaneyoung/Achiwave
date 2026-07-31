from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class Campaign(Base):
    """User-owned objective whose completion state is backend-derived."""

    __tablename__ = "campaigns"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_campaigns_user_id_users",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("id", "user_id", name="uq_campaigns_id_user_id"),
        CheckConstraint(
            "title = btrim(title) AND title <> ''",
            name="ck_campaigns_title_nonblank",
        ),
        CheckConstraint(
            "display_order >= 0",
            name="ck_campaigns_display_order_nonnegative",
        ),
        CheckConstraint(
            "campaign_state IN ('active', 'completed', 'archived')",
            name="ck_campaigns_campaign_state",
        ),
        CheckConstraint(
            "record_version >= 1",
            name="ck_campaigns_record_version_positive",
        ),
        CheckConstraint(
            "campaign_state <> 'completed' OR completed_at IS NOT NULL",
            name="ck_campaigns_completed_timestamp",
        ),
        CheckConstraint(
            "campaign_state <> 'archived' OR archived_at IS NOT NULL",
            name="ck_campaigns_archived_timestamp",
        ),
        Index(
            "ix_campaigns_user_active_order",
            "user_id",
            "display_order",
            "id",
            postgresql_where=text("campaign_state = 'active' AND deleted_at IS NULL"),
        ),
        Index(
            "ix_campaigns_user_archived_at",
            "user_id",
            "archived_at",
            postgresql_where=text("campaign_state = 'archived'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    campaign_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'active'")
    )
    record_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    completion_reason: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    restored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

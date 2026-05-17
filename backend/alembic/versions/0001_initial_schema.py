"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-17 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "works",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("normalized_title", sa.String, nullable=False),
        sa.Column("sort_author", sa.String, nullable=False),
        sa.Column("series", sa.String, nullable=True),
        sa.Column("series_position", sa.Float, nullable=True),
        sa.Column("publication_year", sa.Integer, nullable=True),
        sa.Column("audience", sa.String, nullable=True),
        sa.Column("identifiers", sa.JSON, nullable=False),
        sa.Column("notes", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_works_title", "works", ["title"])
    op.create_index("ix_works_normalized_title", "works", ["normalized_title"])
    op.create_index("ix_works_sort_author", "works", ["sort_author"])
    op.create_index("ix_works_series", "works", ["series"])
    op.create_index("ix_works_audience", "works", ["audience"])

    op.create_table(
        "contributors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("normalized_name", sa.String, nullable=False),
        sa.Column("sort_name", sa.String, nullable=False),
    )
    op.create_index("ix_contributors_name", "contributors", ["name"])
    op.create_index("ix_contributors_normalized_name", "contributors", ["normalized_name"])
    op.create_index("ix_contributors_sort_name", "contributors", ["sort_name"])

    op.create_table(
        "work_contributors",
        sa.Column("work_id", sa.Integer, sa.ForeignKey("works.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("contributor_id", sa.Integer, sa.ForeignKey("contributors.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role", sa.String, primary_key=True),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("work_id", sa.Integer, sa.ForeignKey("works.id", ondelete="SET NULL"), nullable=True),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("format", sa.String, nullable=True),
        sa.Column("source_kind", sa.String, nullable=False),
        sa.Column("source_id", sa.String, nullable=True),
        sa.Column("path", sa.String, nullable=True),
        sa.Column("content_hash", sa.String, nullable=True),
        sa.Column("size_bytes", sa.BigInteger, nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("bitrate", sa.Integer, nullable=True),
        sa.Column("narrator", sa.String, nullable=True),
        sa.Column("abridged", sa.Boolean, nullable=True),
        sa.Column("metadata_blob", sa.JSON, nullable=False),
        sa.Column("first_seen", sa.DateTime, nullable=False),
        sa.Column("last_seen", sa.DateTime, nullable=False),
    )
    op.create_index("ix_assets_work_id", "assets", ["work_id"])
    op.create_index("ix_assets_type", "assets", ["type"])
    op.create_index("ix_assets_source_kind", "assets", ["source_kind"])
    op.create_index("ix_assets_source_id", "assets", ["source_id"])
    op.create_index("ix_assets_content_hash", "assets", ["content_hash"])

    op.create_table(
        "source_records",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_kind", sa.String, nullable=False),
        sa.Column("source_id", sa.String, nullable=False),
        sa.Column("raw", sa.JSON, nullable=False),
        sa.Column("fetched_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_source_records_source_kind", "source_records", ["source_kind"])
    op.create_index("ix_source_records_source_id", "source_records", ["source_id"])

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String, nullable=False, unique=True),
        sa.Column("label", sa.String, nullable=False),
        sa.Column("color", sa.String, nullable=True),
        sa.Column("is_filter", sa.Boolean, nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "work_tags",
        sa.Column("work_id", sa.Integer, sa.ForeignKey("works.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.Integer, sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "review_queue",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("asset_id", sa.Integer, sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_work_id", sa.Integer, sa.ForeignKey("works.id", ondelete="SET NULL"), nullable=True),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("reasons", sa.JSON, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_review_queue_asset_id", "review_queue", ["asset_id"])
    op.create_index("ix_review_queue_status", "review_queue", ["status"])

    op.create_table(
        "library_roots",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("path", sa.String, nullable=False, unique=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_scanned_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("library_roots")
    op.drop_table("review_queue")
    op.drop_table("work_tags")
    op.drop_table("tags")
    op.drop_table("source_records")
    op.drop_table("assets")
    op.drop_table("work_contributors")
    op.drop_table("contributors")
    op.drop_table("works")

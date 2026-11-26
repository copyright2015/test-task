"""Create campaign, offer and stream cache tables."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "countries",
        sa.Column("code", sa.String(length=2), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
    )
    op.bulk_insert(
        sa.table("countries", sa.column("code", sa.String()), sa.column("name", sa.String())),
        [
            {"code": "AU", "name": "Australia"}, {"code": "BR", "name": "Brazil"},
            {"code": "CA", "name": "Canada"}, {"code": "DE", "name": "Germany"},
            {"code": "ES", "name": "Spain"}, {"code": "FR", "name": "France"},
            {"code": "GB", "name": "United Kingdom"}, {"code": "ID", "name": "Indonesia"},
            {"code": "IN", "name": "India"}, {"code": "IT", "name": "Italy"},
            {"code": "JP", "name": "Japan"}, {"code": "MX", "name": "Mexico"},
            {"code": "NL", "name": "Netherlands"}, {"code": "PH", "name": "Philippines"},
            {"code": "PL", "name": "Poland"}, {"code": "RU", "name": "Russia"},
            {"code": "TH", "name": "Thailand"}, {"code": "TR", "name": "Turkey"},
            {"code": "UA", "name": "Ukraine"}, {"code": "US", "name": "United States"},
            {"code": "VN", "name": "Vietnam"}, {"code": "ZA", "name": "South Africa"},
        ],
    )
    op.create_table(
        "campaigns",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("alias", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=True),
        sa.Column("raw_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("synced_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "offers",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=True),
        sa.Column("raw_json", sa.Text(), nullable=False, server_default="{}"),
    )
    op.create_table(
        "streams",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("campaign_id", sa.String(), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("raw_json", sa.Text(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_streams_campaign_id", "streams", ["campaign_id"])
    op.create_table(
        "stream_offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("stream_id", sa.String(), sa.ForeignKey("streams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("offer_id", sa.String(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="0"),
        sa.Column("fixed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("raw_json", sa.Text(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_stream_offers_stream_id", "stream_offers", ["stream_id"])


def downgrade() -> None:
    op.drop_table("stream_offers")
    op.drop_index("ix_streams_campaign_id", table_name="streams")
    op.drop_table("streams")
    op.drop_table("offers")
    op.drop_table("campaigns")
    op.drop_table("countries")

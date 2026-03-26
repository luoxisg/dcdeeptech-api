"""Initial schema — all tables

Revision ID: 0001
Revises:
Create Date: 2025-03-26 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── ENUMS ─────────────────────────────────────────────────────────────────
    userrole = postgresql.ENUM("user", "admin", name="userrole", create_type=False)
    userrole.create(op.get_bind(), checkfirst=True)

    userstatus = postgresql.ENUM("active", "disabled", "pending", name="userstatus", create_type=False)
    userstatus.create(op.get_bind(), checkfirst=True)

    apikeystatus = postgresql.ENUM("active", "revoked", name="apikeystatus", create_type=False)
    apikeystatus.create(op.get_bind(), checkfirst=True)

    modelprovider = postgresql.ENUM("openrouter", "vllm", "dahua", "custom", name="modelprovider", create_type=False)
    modelprovider.create(op.get_bind(), checkfirst=True)

    modelmodality = postgresql.ENUM("text", "vision", name="modelmodality", create_type=False)
    modelmodality.create(op.get_bind(), checkfirst=True)

    transactiontype = postgresql.ENUM("topup", "debit", "refund", "manual_adjustment", name="transactiontype", create_type=False)
    transactiontype.create(op.get_bind(), checkfirst=True)

    # ── USERS ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("role", sa.Enum("user", "admin", name="userrole"), nullable=False, server_default="user"),
        sa.Column("status", sa.Enum("active", "disabled", "pending", name="userstatus"), nullable=False, server_default="active"),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── API KEYS ──────────────────────────────────────────────────────────────
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_prefix", sa.String(24), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("status", sa.Enum("active", "revoked", name="apikeystatus"), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"])
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)

    # ── MODEL CATALOG ─────────────────────────────────────────────────────────
    op.create_table(
        "model_catalog",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("public_name", sa.String(100), nullable=False),
        sa.Column("provider", sa.Enum("openrouter", "vllm", "dahua", "custom", name="modelprovider"), nullable=False),
        sa.Column("upstream_model", sa.String(200), nullable=False),
        sa.Column("modality", sa.Enum("text", "vision", name="modelmodality"), nullable=False, server_default="text"),
        sa.Column("input_price_per_1k", sa.Numeric(10, 6), nullable=False, server_default="0.0"),
        sa.Column("output_price_per_1k", sa.Numeric(10, 6), nullable=False, server_default="0.0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_model_catalog_public_name", "model_catalog", ["public_name"], unique=True)

    # ── WALLETS ───────────────────────────────────────────────────────────────
    op.create_table(
        "wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("balance", sa.Numeric(12, 6), nullable=False, server_default="0.0"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── TRANSACTIONS ──────────────────────────────────────────────────────────
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.Enum("topup", "debit", "refund", "manual_adjustment", name="transactiontype"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 6), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("reference_type", sa.String(50), nullable=True),
        sa.Column("reference_id", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])

    # ── USAGE LOGS ────────────────────────────────────────────────────────────
    op.create_table(
        "usage_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", sa.String(100), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("upstream_model", sa.String(200), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_input", sa.Numeric(12, 8), nullable=False, server_default="0.0"),
        sa.Column("cost_output", sa.Numeric(12, 8), nullable=False, server_default="0.0"),
        sa.Column("total_cost", sa.Numeric(12, 8), nullable=False, server_default="0.0"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=False, server_default="200"),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("client_ip", sa.String(45), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_usage_logs_request_id", "usage_logs", ["request_id"], unique=True)
    op.create_index("ix_usage_logs_user_id", "usage_logs", ["user_id"])
    op.create_index("ix_usage_logs_created_at", "usage_logs", ["created_at"])

    # ── SEED: default model catalog entries ───────────────────────────────────
    op.execute("""
        INSERT INTO model_catalog
            (id, public_name, provider, upstream_model, modality,
             input_price_per_1k, output_price_per_1k, enabled, is_public)
        VALUES
            (gen_random_uuid(), 'claude-3-5-sonnet',   'openrouter', 'anthropic/claude-3.5-sonnet', 'text', 0.003000, 0.015000, true, true),
            (gen_random_uuid(), 'claude-3-haiku',       'openrouter', 'anthropic/claude-3-haiku',    'text', 0.000250, 0.001250, true, true),
            (gen_random_uuid(), 'gpt-4o',               'openrouter', 'openai/gpt-4o',               'text', 0.005000, 0.015000, true, true),
            (gen_random_uuid(), 'gpt-4o-mini',          'openrouter', 'openai/gpt-4o-mini',          'text', 0.000150, 0.000600, true, true),
            (gen_random_uuid(), 'gemini-1.5-pro',       'openrouter', 'google/gemini-pro-1.5',       'text', 0.003500, 0.010500, true, true),
            (gen_random_uuid(), 'llama-3.3-70b',        'openrouter', 'meta-llama/llama-3.3-70b-instruct', 'text', 0.000390, 0.000390, true, true),
            (gen_random_uuid(), 'deepseek-v3',          'openrouter', 'deepseek/deepseek-chat',      'text', 0.000270, 0.001100, true, true)
        ON CONFLICT (public_name) DO NOTHING;
    """)


def downgrade() -> None:
    op.drop_table("usage_logs")
    op.drop_table("transactions")
    op.drop_table("wallets")
    op.drop_table("model_catalog")
    op.drop_table("api_keys")
    op.drop_table("users")

    # Drop enums
    for name in ["userrole", "userstatus", "apikeystatus", "modelprovider", "modelmodality", "transactiontype"]:
        op.execute(f"DROP TYPE IF EXISTS {name}")

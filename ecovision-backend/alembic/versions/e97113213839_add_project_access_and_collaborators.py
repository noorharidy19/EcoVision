"""add project access and collaborators

Revision ID: e97113213839
Revises: ffe64db93179
Create Date: 2026-03-13 16:27:13.465713

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e97113213839'
down_revision: Union[str, Sequence[str], None] = 'ffe64db93179'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # project_access_requests table
    op.create_table(
        "project_access_requests",

        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("requester_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),

        sa.Column(
            "status",
            sa.Enum("PENDING", "ACCEPTED", "DECLINED", name="requeststatus"),
            nullable=False,
            server_default="PENDING"
        ),

        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("responded_at", sa.DateTime(), nullable=True)
    )


    # project_collaborators table
    op.create_table(
        "project_collaborators",

        sa.Column("id", sa.Integer(), primary_key=True),

        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id"),
            nullable=False
        ),

        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False
        ),

        sa.Column(
            "role",
            sa.Enum("OWNER","COLLABORATOR", name="projectrole"),
            nullable=False,
            server_default="COLLABORATOR"
        ),

        sa.Column(
            "added_at",
            sa.DateTime(),
            server_default=sa.func.now()
        ),

        sa.UniqueConstraint(
            "project_id",
            "user_id",
            name="unique_project_collaborator"
        )
    )


def downgrade() -> None:

    op.drop_table("project_collaborators")

    op.drop_table("project_access_requests")

    sa.Enum(name="projectrole").drop(op.get_bind(), checkfirst=True)

    sa.Enum(name="requeststatus").drop(op.get_bind(), checkfirst=True)
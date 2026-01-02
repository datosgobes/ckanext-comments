# Copyright (C) 2025 Entidad Pública Empresarial Red.es
#
# This file is part of "comments (datos.gob.es)".
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Init tables

Revision ID: 275515c51af1
Revises:
Create Date: 2021-03-24 15:03:16.549798

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "275515c51af1"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "comments_threads",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("subject_id", sa.Text, nullable=False),
        sa.Column("subject_type", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Index("subject_idx", "subject_id", "subject_type", unique=True),
    )
    op.create_table(
        "comments_comments",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column(
            "thread_id",
            sa.Text,
            sa.ForeignKey("comments_threads.id"),
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("author_id", sa.Text, nullable=False),
        sa.Column("author_type", sa.Text, nullable=False),
        sa.Column("state", sa.Text, nullable=False),
        sa.Column("email", sa.Text, nullable=True),
        sa.Column("username", sa.Text, nullable=True),
        sa.Column("consent", sa.BOOLEAN, nullable=True),
        sa.Column(
            "reply_to_id",
            sa.Text,
            sa.ForeignKey("comments_comments.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("modified_at", sa.DateTime, nullable=True),
        sa.Index("author_idx", "author_id", "author_type"),
    )


def downgrade():
    op.drop_table("comments_comments")
    op.drop_table("comments_threads")

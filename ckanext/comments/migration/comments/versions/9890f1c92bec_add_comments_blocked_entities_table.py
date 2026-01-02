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

"""Add comments_blocked_entities table

Revision ID: 9890f1c92bec
Revises: acd1862c2e17
Create Date: 2025-04-08 16:46:45.731797

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9890f1c92bec'
down_revision = 'acd1862c2e17'
branch_labels = None
depends_on = None


def upgrade():
    
    op.create_table(
        "comments_blocked_entities",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("subject_id", sa.Text, nullable=False),
        sa.Column("subject_type", sa.Text, nullable=False),
        sa.Column(
            "blocked_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Index("blcoked_entity_idx", "subject_id", "subject_type", unique=True),
    )


def downgrade():
    op.drop_table("comments_blocked_entities")

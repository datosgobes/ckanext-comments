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

"""add cascade to comments

Revision ID: 910f3d575038
Revises: 275515c51af1
Create Date: 2023-10-06 22:54:18.933232

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "910f3d575038"
down_revision = "275515c51af1"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("comments_comments_thread_id_fkey", "comments_comments")
    op.drop_constraint("comments_comments_reply_to_id_fkey", "comments_comments")

    op.create_foreign_key(
        "comments_comments_thread_id_fkey",
        "comments_comments",
        "comments_threads",
        ["thread_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "comments_comments_reply_to_id_fkey",
        "comments_comments",
        "comments_comments",
        ["reply_to_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    pass

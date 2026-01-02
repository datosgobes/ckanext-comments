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

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Text, BOOLEAN
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import foreign, relationship

import ckan.model as model
from ckan.model.types import make_uuid

from ckanext.comments.exceptions import UnsupportedAuthorType

from . import Thread
from .base import Base

foreign: Any = foreign
log = logging.getLogger(__name__)

Author = model.User
AuthorGetter = Callable[[str], Optional[Author]]


class Comment(Base):
    __tablename__ = "comments_comments"
    _author_getters: dict[str, AuthorGetter] = {"user": model.User.get}

    class State:
        draft = "draft"
        approved = "approved"

    id = Column(Text, primary_key=True, default=make_uuid)

    thread_id = Column(Text, ForeignKey(Thread.id), nullable=False)

    content = Column(Text, nullable=False)

    author_id = Column(Text, nullable=False)
    author_type = Column(Text, nullable=False)

    state = Column(Text, nullable=False, default=State.draft)

    reply_to_id = Column(Text, ForeignKey(id), nullable=True, index=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    modified_at = Column(DateTime, nullable=True)

    extras = Column(JSONB, nullable=False, default=dict)

    email = Column(Text, nullable=True)
    username = Column(Text, nullable=True)
    consent = Column(BOOLEAN, nullable=True)

    thread: Any = relationship(Thread, single_parent=True)

    user: Any = relationship(
        model.User,
        backref="comments",
        primaryjoin=(author_type == "user") & (model.User.id == foreign(author_id)),
        single_parent=True,
    )

    reply_to: Any = relationship(
        "Comment", primaryjoin=id == reply_to_id, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            "Comment("
            f"id={self.id!r},"
            f"thread_id={self.thread_id!r},"
            f"author_id={self.author_id!r},"
            f"author_type={self.author_type!r},"
            f"reply_to_id={self.reply_to_id!r},"
            f"email={self.email!r},"
            f"username={self.username!r},"
            f"consent={self.consent!r},"
            ")"
        )

    @classmethod
    def by_thread(cls, thread_id: str):
        return (
            model.Session.query(cls)
            .filter(cls.thread_id == thread_id)
            .order_by(cls.created_at)
        )

    def approve(self) -> None:
        self.state = self.State.approved
    
    def draft(self) -> None:
        self.state = self.State.draft

    def is_approved(self) -> bool:
        return self.state == self.State.approved

    def is_authored_by(self, name: str) -> bool:
        if self.user:
            return name == self.user.name or name == self.user.id
        return False

    def get_author(self) -> Optional[Author]:
        try:
            getter = self._author_getters[self.author_type]  
        except KeyError:
            log.error("Unknown subject type: %s", self.author_type)
            raise UnsupportedAuthorType(self.author_type)
        return getter(self.author_id)

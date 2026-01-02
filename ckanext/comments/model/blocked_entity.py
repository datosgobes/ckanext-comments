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
from typing import (
    Any,
    Callable,
    Literal,
    Optional,
    Union,
    cast,
    overload,
)
from werkzeug.utils import import_string

from sqlalchemy import Column, DateTime, Text
from sqlalchemy.orm import Query

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.model.types import make_uuid

from ckanext.comments.exceptions import UnsupportedSubjectType

from .base import Base

log = logging.getLogger(__name__)

Subject = Union[model.Package, model.Resource, model.User, model.Group]
SubjectGetter = Callable[[str], Optional[Subject]]


class BlockedEntity(Base):
    __tablename__ = "comments_blocked_entities"
    _subject_getters: dict[str, SubjectGetter] = {
        "package": model.Package.get,
        "resource": model.Resource.get,
        "user": model.User.get,
        "group": model.Group.get,
    }

    id = Column(Text, primary_key=True, default=make_uuid)
    subject_id = Column(Text, nullable=False)
    subject_type = Column(Text, nullable=False)
    blocked_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return "BlockedEntity(" f"id={self.id!r}, " f"subject_type={self.subject_type!r}, " ")"

    def get_subject(self) -> Optional[Subject]:
        return self.locate_subject(cast(str, self.subject_type), self.subject_id)

    @classmethod
    def locate_subject(cls, subject_type: str, subject_id: Any):
        option = tk.config.get(f"ckanext.comments.subject.{subject_type}_getter")
        getter = import_string(option, True) if option else None
        if not getter and subject_type in cls._subject_getters:
            getter = cls._subject_getters[subject_type]

        if not getter:
            raise UnsupportedSubjectType(subject_type)

        return getter(subject_id)

    @classmethod
    def for_subject(
        cls, type_: str, id_: str
    ) -> Optional[BlockedEntity]:
        if subject := cls.locate_subject(type_, id_):
            id_ = str(subject.id)
        log.info(f'id_ = {id_}')
        blocked_entity = (
            model.Session.query(cls)
            .filter(cls.subject_type == type_, cls.subject_id == id_)
            .one_or_none()
        )

        log.info(f'blocked_entity = {blocked_entity}')
        return blocked_entity

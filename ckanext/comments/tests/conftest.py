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

import pytest

import ckan.model as model
from ckan.cli.db import _resolve_alembic_config

import ckanext.comments.tests.factories as factories


@pytest.fixture
def clean_db(reset_db, monkeypatch):
    reset_db()
    monkeypatch.setattr(model.repo, "_alembic_ini", _resolve_alembic_config("comments"))
    model.repo.upgrade_db()


@pytest.fixture
def Thread():
    return factories.Thread


@pytest.fixture
def Comment():
    return factories.Comment

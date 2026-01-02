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
import ckan.tests.factories as factories

import ckanext.comments.model as c_model
from ckanext.comments.exceptions import UnsupportedSubjectType


@pytest.mark.usefixtures("clean_db")
class TestThread:
    def test_comments(self, Thread, Comment):
        th = Thread()
        thread = model.Session.query(c_model.Thread).filter_by(id=th["id"]).one()
        assert thread.comments().count() == 0

        Comment(thread=th)
        assert thread.comments().count() == 1

        Comment(thread=th)
        assert thread.comments().count() == 2

        Comment()
        assert thread.comments().count() == 2

    def test_get_subject(self, Thread):
        dataset = factories.Dataset()
        th = c_model.Thread(subject_type="taxes")

        with pytest.raises(UnsupportedSubjectType):
            th.get_subject()

        th.subject_type = "package"
        assert th.get_subject() is None

        th.subject_id = dataset["id"]
        assert th.get_subject().name == dataset["name"]

    def test_for_subject(self):
        dataset = factories.Dataset()
        assert c_model.Thread.for_subject("package", dataset["id"]) is None

        th = c_model.Thread.for_subject("package", dataset["id"], init_missing=True)
        assert th.id is None
        assert th.subject_type == "package"
        assert th.subject_id == dataset["id"]

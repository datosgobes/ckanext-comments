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
from ckan.tests.helpers import call_action

import ckanext.comments.model as c_model
from ckanext.comments.exceptions import UnsupportedAuthorType


def test_approval():
    c = c_model.Comment(state=c_model.Comment.State.draft)
    assert not c.is_approved()
    c.approve()
    assert c.is_approved()


@pytest.mark.usefixtures("clean_db")
class TestComment:
    def test_authored_by(self, Comment):
        author = factories.User()
        not_author = factories.User()
        comment = Comment(author_type="user", author_id=author["id"])
        c = model.Session.query(c_model.Comment).filter_by(id=comment["id"]).one()
        assert c.is_authored_by(author["id"])
        assert c.is_authored_by(author["name"])
        assert not c.is_authored_by(not_author["id"])
        assert not c.is_authored_by(not_author["name"])

    def test_by_thread(self, Comment, Thread):
        th = Thread()
        c1 = Comment(thread=th)
        c2 = Comment(thread=th)
        c3 = Comment()

        g1, g2, g3 = (
            [c.id for c in group]
            for group in [
                c_model.Comment.by_thread(c["thread_id"]) for c in [c1, c2, c3]
            ]
        )

        assert g1 == g2
        assert g1 == [c1["id"], c2["id"]]
        assert g3 == [c3["id"]]

    def test_get_author(self):
        user = factories.User()
        comment = c_model.Comment(author_type="fairy")
        with pytest.raises(UnsupportedAuthorType):
            comment.get_author()

        comment.author_type = "user"
        assert comment.get_author() is None

        comment.author_id = user["id"]
        assert comment.get_author().name == user["name"]

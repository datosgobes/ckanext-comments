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

import datetime as dt

import pytest

import ckan.model as model
import ckan.tests.factories as factories
from ckan.tests.helpers import call_action

import ckanext.comments.model as c_model
from ckanext.comments.model.dictize import comment_dictize, thread_dictize


@pytest.mark.usefixtures("clean_db")
class TestDictize:
    def test_thread_dictize(self, Thread, Comment):
        thread = Thread()
        comment = Comment(thread=thread)
        call_action("comments_comment_approve", id=comment["id"])

        th = model.Session.query(c_model.Thread).filter_by(id=thread["id"]).one()
        dictized = thread_dictize(th, {"model": model, "user": ""})
        assert thread == dictized

        dictized = thread_dictize(
            th, {"model": model, "user": "", "include_comments": True}
        )
        comments = dictized.pop("comments")
        dictized["comments"] = None
        assert thread == dictized
        assert len(comments) == 1

    def test_comment_dictize(self, Comment):
        author = factories.User()
        comment = Comment(author_type="user", author_id=author["id"])
        c = model.Session.query(c_model.Comment).filter_by(id=comment["id"]).one()

        assert comment_dictize(c, {"model": model}) == comment

        dictized = comment_dictize(c, {"model": model, "include_author": True})
        dictized_author = dictized.pop("author")
        assert dictized == comment

        author.pop("email")
        author.pop("apikey")
        assert author == dictized_author

    def test_thread_dictize_with_comments(self, Comment, Thread):
        sysadmin = factories.Sysadmin()
        user = factories.User()
        th = Thread()
        c1 = Comment(thread=th)
        c2 = Comment(thread=th, user=user)
        c3 = Comment(thread=th)
        call_action("comments_comment_approve", id=c1["id"])
        thread = model.Session.query(c_model.Thread).filter_by(id=th["id"]).one()
        comments = thread_dictize(
            thread, {"model": model, "user": "", "include_comments": True}
        )["comments"]
        assert len(comments) == 1
        assert "author" not in comments[0]
        assert comments[0]["approved"]

        comments = thread_dictize(
            thread,
            {
                "model": model,
                "user": "",
                "include_comments": True,
                "include_author": True,
            },
        )["comments"]
        assert len(comments) == 1
        assert "author" in comments[0]

        comments = thread_dictize(
            thread,
            {
                "model": model,
                "user": user["name"],
                "include_comments": True,
                "include_author": True,
            },
        )["comments"]
        assert len(comments) == 2
        assert comments[0]["approved"]
        assert not comments[1]["approved"]

        comments = thread_dictize(
            thread,
            {
                "model": model,
                "user": "",
                "include_comments": True,
                "ignore_auth": True,
            },
        )["comments"]
        assert len(comments) == 3
        assert not comments[1]["approved"]
        assert not comments[2]["approved"]

        comments = thread_dictize(
            thread,
            {
                "model": model,
                "user": sysadmin["name"],
                "include_comments": True,
                "include_author": True,
            },
        )["comments"]
        assert len(comments) == 3

    def test_thread_dictize_comments_filter_by_date(self, Comment, Thread):
        th = Thread()
        c1 = Comment(thread=th)
        Comment(thread=th)
        sysadmin = factories.Sysadmin()

        thread = model.Session.query(c_model.Thread).filter_by(id=th["id"]).one()

        comments = thread_dictize(
            thread,
            {
                "model": model,
                "user": sysadmin["name"],
                "include_comments": True,
            },
        )["comments"]
        assert len(comments) == 2

        comments = thread_dictize(
            thread,
            {
                "model": model,
                "user": sysadmin["name"],
                "include_comments": True,
                "after_date": (dt.datetime.now() + dt.timedelta(days=1)).isoformat(),
            },
        )["comments"]
        assert len(comments) == 0

        comment = model.Session.query(c_model.Comment).get(c1.get("id"))
        comment.created_at = dt.datetime.now() - dt.timedelta(days=3)
        model.Session.commit()

        comments = thread_dictize(
            thread,
            {
                "model": model,
                "user": sysadmin["name"],
                "include_comments": True,
                "after_date": (dt.datetime.now() - dt.timedelta(days=1)).isoformat(),
            },
        )["comments"]
        assert len(comments) == 1

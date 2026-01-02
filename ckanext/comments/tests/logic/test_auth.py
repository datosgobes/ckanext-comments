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
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckan.tests.helpers import call_action, call_auth

from ckanext.comments import config


@pytest.mark.usefixtures("clean_db")
class TestAuth:
    @pytest.mark.parametrize(
        "func,results",
        [
            #  auth, (anon, user, admin)
            ("thread_create", (False, True, True)),
            ("thread_show", (True, True, True)),
            ("thread_delete", (False, False, True)),
            ("comment_create", (False, True, True)),
            ("reply_create", (False, True, True)),
            ("comment_approve", (False, False, True)),
            ("comment_delete", (False, False, True)),
        ],
    )
    def test_basic_permissions(self, func, results):
        users = ("", factories.User()["name"], factories.Sysadmin()["name"])
        for user, result in zip(users, results):
            context = {"model": model, "user": user}
            auth = f"comments_{func}"
            if result:
                assert call_auth(auth, context)
            else:
                with pytest.raises(tk.NotAuthorized):
                    call_auth(auth, context)

    def test_comment_show(self, Comment):
        user = factories.User()
        anon_ctx = {"model": model, "user": ""}
        user_ctx = {"model": model, "user": user["name"]}
        comment = Comment(user=user)
        with pytest.raises(tk.NotAuthorized):
            call_auth("comments_comment_show", anon_ctx.copy(), id=comment["id"])
        assert call_auth("comments_comment_show", user_ctx.copy(), id=comment["id"])

        call_action("comments_comment_approve", id=comment["id"])
        assert call_auth("comments_comment_show", anon_ctx.copy(), id=comment["id"])
        assert call_auth("comments_comment_show", user_ctx.copy(), id=comment["id"])

    @pytest.mark.ckan_config(config.CONFIG_DRAFT_EDITS_BY_AUTHOR, False)
    def test_comment_update(self, Comment, monkeypatch, ckan_config):
        user = factories.User()
        user_ctx = {"model": model, "user": user["name"]}
        another_user_ctx = {"model": model, "user": factories.User()["name"]}
        comment = Comment(user=user)

        with pytest.raises(tk.NotAuthorized):
            assert call_auth(
                "comments_comment_update", user_ctx.copy(), id=comment["id"]
            )

        monkeypatch.setitem(ckan_config, config.CONFIG_DRAFT_EDITS_BY_AUTHOR, True)

        with pytest.raises(tk.NotAuthorized):
            call_auth(
                "comments_comment_update",
                another_user_ctx.copy(),
                id=comment["id"],
            )
        assert call_auth("comments_comment_update", user_ctx.copy(), id=comment["id"])

        call_action("comments_comment_approve", id=comment["id"])

        with pytest.raises(tk.NotAuthorized):
            call_auth(
                "comments_comment_update",
                user_ctx.copy(),
                id=comment["id"],
            )
        with pytest.raises(tk.NotAuthorized):
            call_auth(
                "comments_comment_update",
                another_user_ctx.copy(),
                id=comment["id"],
            )

        monkeypatch.setitem(ckan_config, config.CONFIG_APPROVED_EDITS_BY_AUTHOR, True)
        with pytest.raises(tk.NotAuthorized):
            call_auth(
                "comments_comment_update",
                another_user_ctx.copy(),
                id=comment["id"],
            )

        assert call_auth("comments_comment_update", user_ctx.copy(), id=comment["id"])

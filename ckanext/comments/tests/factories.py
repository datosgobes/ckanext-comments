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

import factory
from factory.fuzzy import FuzzyText

import ckan.tests.factories as factories
import ckan.tests.helpers as helpers

import ckanext.comments.model as model


class Thread(factory.Factory):
    """A factory class for creating CKAN datasets."""

    class Meta:
        model = model.Thread

    subject_id = factory.LazyAttribute(lambda _: factories.Dataset()["id"])
    subject_type = "package"

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        context = {"user": factories._get_action_user_name(kwargs)}
        thread_dict = helpers.call_action(
            "comments_thread_create", context=context, **kwargs
        )
        return thread_dict


class Comment(factory.Factory):
    """A factory class for creating CKAN datasets."""

    class Meta:
        model = model.Comment

    thread = factory.LazyAttribute(lambda _: Thread())
    content = FuzzyText("content:", 140)

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        context = {"user": factories._get_action_user_name(kwargs)}

        thread = kwargs.pop("thread")
        kwargs["subject_id"] = thread["subject_id"]
        kwargs["subject_type"] = thread["subject_type"]

        comment_dict = helpers.call_action(
            "comments_comment_create", context=context, **kwargs
        )
        return comment_dict

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

import ckan.plugins.toolkit as tk
from ckan.logic.schema import validator_args
import logging
log = logging.getLogger(__name__)

@validator_args
def thread_create(not_empty, unicode_safe):
    return {
        "subject_id": [
            not_empty,
            unicode_safe,
        ],
        "subject_type": [
            not_empty,
            unicode_safe,
        ],
    }


@validator_args
def thread_show(default, boolean_validator, ignore_missing, isodate):
    schema = thread_create()
    schema.update(
        {
            "newest_first": [default(False), boolean_validator],
            "init_missing": [default(False), boolean_validator],
            "include_comments": [default(False), boolean_validator],
            "include_author": [default(False), boolean_validator],
            "combine_comments": [default(False), boolean_validator],
            "after_date": [ignore_missing, isodate],
        }
    )
    return schema


@validator_args
def thread_delete(not_empty):
    return {"id": [not_empty]}


@validator_args
def comment_create(
    not_empty,
    unicode_safe,
    one_of,
    default,
    boolean_validator,
    ignore_missing,
    convert_to_json_if_string,
    dict_only,
):
    return {
        "subject_id": [not_empty, unicode_safe],
        "subject_type": [
            not_empty,
            unicode_safe,
        ],
        "content": [
            not_empty,
        ],
        "author_id": [
            ignore_missing,
        ],
        "author_type": [default("user"), one_of(["user"])],
        "reply_to_id": [
            ignore_missing,
            tk.get_validator("comments_comment_exists"),
        ],
        "create_thread": [default(False), boolean_validator],
        "email": [
            tk.get_validator("comments_not_empty_if_anonymous_email"),
        ],
        "username": [],
        "consent": [
            tk.get_validator("comments_not_empty_if_anonymous_consent"),
        ],
        "url": [
            tk.get_validator("comments_is_a_bot"),
        ],
        "extras": [default("{}"), convert_to_json_if_string, dict_only],
    }


@validator_args
def comment_show(not_empty):
    return {"id": [not_empty]}


@validator_args
def comment_approve(not_empty):
    return {"id": [not_empty]}

@validator_args
def comment_draft(not_empty):
    return {"id": [not_empty]}

@validator_args
def comment_delete(not_empty):
    return {"id": [not_empty]}


@validator_args
def comment_update(not_empty):
    return {
        "id": [not_empty],
        "content": [not_empty],
    }

@validator_args
def blocked_entity_delete(not_empty):
    return {"subject_id": [not_empty],
            "subject_type": [not_empty]}

@validator_args
def blocked_entity_create(not_empty, unicode_safe):
    return {
        "subject_id": [
            not_empty,
            unicode_safe,
        ],
        "subject_type": [
            not_empty,
            unicode_safe,
        ],
    }

@validator_args
def blocked_entity_show(not_empty):
    return {"subject_id": [not_empty],
            "subject_type": [not_empty]}

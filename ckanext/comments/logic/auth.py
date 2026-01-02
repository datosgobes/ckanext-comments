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

import ckan.plugins.toolkit as tk

from ckanext.comments.model import Comment

from .. import config
from ..utils import is_moderator

log = logging.getLogger(__name__)
_auth = {}


def _can_edit(state: str, by_author: bool = False) -> bool:
    if state == Comment.State.draft:
        if by_author:
            return config.allow_draft_edits_by_author()
        return config.allow_draft_edits()
    elif state == Comment.State.approved:
        if by_author:
            return config.allow_approved_edits_by_author()
        return config.allow_approved_edits()

    log.warning("Unexpected comment state: %s", state)
    return False


def auth(func):
    func.__name__ = f"comments_{func.__name__}"
    _auth[func.__name__] = func
    return func


def get_auth_functions():
    return _auth.copy()


@auth
def thread_create(context, data_dict):
    return {"success": True}


@auth
@tk.auth_allow_anonymous_access
def thread_show(context, data_dict):
    return {"success": True}


@auth
def thread_delete(context, data_dict):
    return {"success": False}


@auth
def comment_create(context, data_dict):
    return {"success": True}


@auth
def reply_create(context, data_dict):
    return {"success": True}


@auth
@tk.auth_allow_anonymous_access
def comment_show(context, data_dict):
    id = tk.get_or_bust(data_dict, "id")
    comment = context["session"].query(Comment).filter(Comment.id == id).one_or_none()

    if not comment:
        raise tk.ObjectNotFound("Comment not found")
    return {"success": comment.is_approved() or comment.is_authored_by(context["user"])}


@auth
def comment_approve(context, data_dict):
    id = data_dict.get("id")
    if not id:
        return {"success": False}

    comment = context["session"].query(Comment).filter(Comment.id == id).one_or_none()
    if not comment:
        return {"success": False}
    return {"success": is_moderator(context["auth_user_obj"], comment, comment.thread)}

@auth
def comment_draft(context, data_dict):
    id = data_dict.get("id")
    if not id:
        return {"success": False}
    comment = context["session"].query(Comment).filter(Comment.id == id).one_or_none()
    if not comment:
        return {"success": False}
    return {"success": is_moderator(context["auth_user_obj"], comment, comment.thread)}


@auth
def comment_delete(context, data_dict):
    return comment_update(context, data_dict)


@auth
def comment_update(context, data_dict):

    id = data_dict.get("id")
    if not id:
        return {"success": False}

    comment = context["session"].query(Comment).filter(Comment.id == id).one_or_none()
    if not comment:
        return {"success": False}

    by_author = comment.is_authored_by(context["user"])
    
    if is_moderator(context["auth_user_obj"], comment, comment.thread):
        return {"success": _can_edit(comment.state, by_author)}
    return {"success": False}


@auth
@tk.auth_allow_anonymous_access
def blocked_entity_show(context, data_dict):
    return {"success": True}

@auth
def blocked_entity_create(context, data_dict):
    if not _user_is_sysadmin(context):
        return {'success': False, 'msg': tk._('Only sysadmins can block add new comments')}
    else:
        return {'success': True}

@auth
def blocked_entity_delete(context, data_dict):
    if not _user_is_sysadmin(context):
        return {'success': False, 'msg': tk._('Only sysadmins can unblock add new comments')}
    else:
        return {'success': True}


def _user_is_sysadmin(context):
    '''
        Checks if the user defined in the context is a sysadmin

        rtype: boolean
    '''
    model = context['model']
    user = context['user']
    user_obj = model.User.get(user)
    if not user_obj:
        raise tk.Objectpt.ObjectNotFound('User {0} not found').format(user)

    return user_obj.sysadmin

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

from typing import Any, Optional

from datetime import datetime
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.lib.i18n import get_available_locales

from ckanext.comments.model.thread import Subject

from typing import List, Dict
from datetime import datetime

from ckan.common import (
    _, ungettext, g, c, request, session, json
)

from . import config
from .model import Comment
import logging
import re

_helpers = {}

log = logging.getLogger(__name__)
def get_helpers():
    helpers = _helpers.copy()

    if "csrf_input" not in tk.h:
        helpers["csrf_input"] = lambda: ""

    return helpers


def helper(func):
    func.__name__ = f"comments_{func.__name__}"
    _helpers[func.__name__] = func
    return func


@helper
def thread_for(id_: Optional[str], type_: str) -> dict[str, Any]:
    thread = tk.get_action("comments_thread_show")(
        {},
        {
            "subject_id": id_,
            "subject_type": type_,
            "include_comments": True,
            "combine_comments": True,
            "include_author": True,
            "init_missing": True,
        },
    )
    return thread


@helper
def mobile_depth_threshold() -> int:
    return config.mobile_depth_threshold()


@helper
def author_of(id_: str) -> Optional[model.User]:
    comment = model.Session.query(Comment).filter(Comment.id == id_).one_or_none()
    if not comment:
        return None
    return comment.get_author()


@helper
def subject_of(id_: str) -> Optional[Subject]:
    comment = model.Session.query(Comment).filter(Comment.id == id_).one_or_none()
    if not comment:
        return None
    return comment.thread.get_subject()


@helper
def enable_default_dataset_comments() -> bool:
    return config.use_default_dataset_comments()

@helper
def custom_date_comments(timestamp) -> str:
    try:
        fecha = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        fecha = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S')
    
    fecha_formateada = fecha.strftime('%d/%m/%Y - %H:%M')
    return fecha_formateada

def parse_date(date_str: str) -> datetime:
    return datetime.fromisoformat(date_str) if date_str else None

@helper
def order_date(data: List[Dict]) -> List[Dict]:
    return sorted(data, key=lambda x: parse_date(x['modified_at']) or parse_date(x['created_at']), reverse=True)

@helper
def is_html(content):
    return bool(re.search(r'<.*?>', content))

@helper
def get_reply(comment) -> tuple:
    
    reply_to_id = comment.get('reply_to_id', None)
    if not reply_to_id:
       
        return None, None
    else: 
        try:
            
            query = '''
            SELECT cc."content", cc."author_id", cc."username" from comments_comments cc where cc.id = :reply_to_id
            '''

            result = model.Session.execute(query, {'reply_to_id':reply_to_id})
            row = result.fetchone()
            if row:
               
                content, author_id, username = row

                author_name = get_my_author(author_id, comment)
                if username:
                    if  author_name == "anónimo":
                        author_name = username + _(" (not verified)")

                return content, author_name
            else:
                return None, None
                
        except Exception as e:
                log.error('helpers.py comments: No se ha podido obtener el usuario: %s', e)
                return None, None

def is_admin_author(author_id) -> bool:
    
  
    try:
        query = '''
                SELECT u.sysadmin  
                        FROM "user" u 
                        WHERE id IN (  :author_id )'''
        result = model.Session.execute(query, {'author_id':author_id})
        row = result.fetchone()
        if not row:
            return False
        else: 

            sysadmin = row
           
            return sysadmin[0]
    except Exception as e:
            log.error('helpers.py comments: No se ha podido obtener el usuario: %s', e)
            return None, None


def get_my_author(author_id, comment) -> str:
    if not author_id or author_id == 'id_no_encontrado':
       
        username = comment.get('username', None)
        
        if not username:
            return _("anonymous")
        return username
    else: 

        is_admin = is_admin_author(author_id)

        if is_admin:
            return "datos.gob.es"
        else:
        
            try:
                query = '''
                SELECT m.table_id , m.group_id 
                        FROM "member" m 
                        WHERE table_id =  :author_id '''
                result = model.Session.execute(query, {'author_id':author_id})
                row = result.fetchone()  
                table_id, group_id = row
                
                if not group_id:
                    return _("anonymous")
                else:
                    query_organismo = '''
                    select g.title from "group" g where id =  :group_id '''
                    result = model.Session.execute(query_organismo, {'group_id':group_id})
                    row_organismo = result.fetchone()
                    if row_organismo:
                        title = row_organismo[0] 
                        return title
            except Exception as e:
                log.error('helpers.py comments: No se ha podido obtener el usuario: %s', e)
                return None


@helper
def get_organismo(comment) -> str:
    
    author_id = comment.get('author_id', None)
    return get_my_author(author_id,comment)

@helper
def is_a_blocked_entity(id_: Optional[str], type_: str) -> bool:
    blocked_entity = None
    try:
        blocked_entity = tk.get_action("comments_blocked_entity_show")(
            {},
            {
                "subject_id": id_,
                "subject_type": type_
            },
        )
        if blocked_entity:
            return True
    except tk.ObjectNotFound:
        return False
    log.info('return False')
    return False

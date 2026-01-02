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
from typing import Any

import ckan.model as model

import logging
log = logging.getLogger(__name__)
from ckan.plugins.toolkit import config as conf
import sqlalchemy as sa
from sqlalchemy.orm import class_mapper
from sqlalchemy import inspect
from ckan.plugins import toolkit

from . import config

ROLE_ADMINISTRATOR = 'xxx'
ROLE_APORTA = 'yyy'
ROLE_PUBLICADOR = 'zzz'

def comments_is_moderator(user: model.User, comment: Any, thread: Any) -> bool:
    return ( can_approve_comment_by_role(user,None,thread.subject_id) or user.sysadmin)
    


def is_moderator(user: model.User, comment: Any, thread: Any) -> bool:
    func = config.moderator_checker() or comments_is_moderator
    return func(user, comment, thread)

def get_roles_by_author_id(author):
    
    engine = sa.create_engine(conf.get('ckanext.dge_drupal_users.connection'))
    return engine.execute(
        'SELECT ur.roles_target_id role FROM user__roles ur '
        ' INNER JOIN user__field_ckan_user_id u on u.entity_id = ur.entity_id'
        ' WHERE u.field_ckan_user_id_value=%s',
        str(author.id))
   
        

def can_approve_comment_by_role(author,comment,thread_id):
    if author is not None:
           
            rows = get_roles_by_author_id(author)

            for row in rows:
                if row.role == ROLE_ADMINISTRATOR or row.role == ROLE_APORTA:
                    return True
                if row.role == ROLE_PUBLICADOR and user_belong_to_same_organization(author,thread_id):
                    return True
    return False

def user_belong_to_same_organization( author, thread_id):
    email_belong_to = False

    user_author = model.User.get(author.id)
    email_commenting_user = user_author.email
    package = model.Package.get(thread_id)
    members = toolkit.get_action('member_list')(
        data_dict={'id': package.owner_org, 'table_name': 'user', 'capacity': 'editor', 'state': 'active'})

    for member in members:
        user = model.User.get(member[0])
        if user:
            if user.email == email_commenting_user:
            	email_belong_to = True
    return email_belong_to

def obj_to_dict_prefix(obj, prefix=''):
    return {prefix + c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}

def flatten_join_prefix(tup_list):
    return [{**obj_to_dict_prefix(a, 'Comment_'), **obj_to_dict_prefix(b, 'Package_')} for a,b in tup_list]
    
def serialize(model):
    """Transforms a model into a dictionary which can be dumped to JSON."""
    columns = [c.key for c in class_mapper(model.__class__).columns]
    return dict((c, getattr(model, c)) for c in columns)
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
import ckan.plugins.toolkit as tk
import re

import logging
log = logging.getLogger(__name__)

from ckanext.comments.model import Comment

_validators: dict[str, Any] = {}


def validator(func: Any): 
    _validators[f"comments_{func.__name__}"] = func
    return func


def get_validators():
    return _validators.copy()


@validator
def comment_exists(value: Any, context: Any):
    comment = context["session"].query(Comment).filter_by(id=value).one_or_none()
    if not comment:
        raise tk.Invalid("Comment does not exist")
    return value



@validator
def not_empty_if_anonymous_email(key, data, errors, context):
    
    email = data.get(('email',),{})
    user = context.get('user')
    if not user and not email:
        raise tk.Invalid("Campo obligatorio email")
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not user and not re.match(patron, email):
        raise tk.Invalid("Campo obligatorio email no cumple el formato deseado")
    


@validator
def not_empty_if_anonymous_consent(key, data, errors, context):
    
    user = context.get('user')
    consent = data.get(('consent',),{})

    if(consent == ''):
        data[('consent',)] = True
        consent = True
    else:
        data[('consent',)] = False
        consent = False

    if not user and (consent == False ):
        raise tk.Invalid("Campo obligatorio consentimiento")



@validator
def is_a_bot(key, data, errors, context):
    is_a_bot = data.get(('url',),{})
    if(is_a_bot is not None):
        raise tk.Invalid("Formulario no valido") 


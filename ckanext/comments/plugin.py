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

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckan.common import c

import ckanext.comments.helpers as helpers
import ckanext.comments.logic.action as action
import ckanext.comments.logic.auth as auth
import ckanext.comments.logic.validators as validators
import json

import ckan.model as model

from ckan.lib.plugins import DefaultTranslation
from ckan.plugins.toolkit import config

from flask import Blueprint, request, jsonify

import logging


try:
    config_declarations = tk.blanket.config_declarations
except AttributeError:
    config_declarations = lambda cls: cls

log = logging.getLogger("ckanext.comments")

# Define el Blueprint
myextension_blueprint = Blueprint('comments', __name__)

# Get is frontend
def is_frontend():
    is_frontend = False
    config_is_frontend = config.get('ckanext.dge.is_frontend', None)
    if config_is_frontend and config_is_frontend.lower() == 'true':
        is_frontend = True
    return is_frontend


@myextension_blueprint.route('/api/3/comments', methods=['GET'])
def getAllComments():
    
    api_key = request.headers.get('Authorization')
 
    user_obj = model.Session.query(model.User).filter_by(apikey=api_key).first()

    if user_obj:
        return action.get_all_comments_ckan_from_package()
    else:
        response_data = {
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "Unauthorized access"
        }
        response = jsonify(response_data)
        response.status_code = 401
        return response
    
    
    
@myextension_blueprint.route('/api/3/comments/userId', methods=['GET'])
def getCommentsByPublicadorId():
    api_key = request.headers.get('Authorization')
 
    user_obj = model.Session.query(model.User).filter_by(apikey=api_key).first()
    ckan_user_id= request.args.get('ckan_user_id')
    if user_obj:
        return action.get_all_comments_ckan_from_package_by_user(ckan_user_id)
    else:
        response_data = {
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "Unauthorized access"
        }
        response = jsonify(response_data)
        response.status_code = 401
        return response

@config_declarations
class CommentsPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IBlueprint)
    if is_frontend():
        plugins.implements(plugins.ITranslation, inherit=True)
 
    def get_blueprint(self):
        return myextension_blueprint

    # IConfigurer

    def update_config(self, config_):
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
        tk.add_resource("assets", "comments")

    # IAuthFunctions

    def get_auth_functions(self):
        return auth.get_auth_functions()

    # IActions

    def get_actions(self):
        return action.get_actions()

    # ITemplateHelpers

    def get_helpers(self):
        return helpers.get_helpers()

    # IValidators

    def get_validators(self):
        return validators.get_validators()

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

from datetime import datetime


import ckan.lib.helpers as h

from ckan.plugins import toolkit
import ckan.model as model
import sqlalchemy as sa
from sqlalchemy.ext.declarative import DeclarativeMeta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from ckan.lib.mailer import MailerException

import ckan.plugins.toolkit as tk
from ckan.logic import validate
from ckan.plugins.toolkit import config as conf
from ckan.common import  _
from ..helpers import is_a_blocked_entity

import json

import ckanext.comments.logic.schema as schema
from ckanext.comments.model import Comment, Thread, BlockedEntity
from ckanext.comments.model.dictize import get_dictizer

import ckan.lib.helpers as h

from ..utils import get_roles_by_author_id, serialize,flatten_join_prefix

from .. import config, signals

import logging
log = logging.getLogger(__name__)

ROLE_ADMINISTRATOR = 'zzzz'
ROLE_APORTA = 'yyyy'
ROLE_PUBLICADOR = 'xxxx'

_actions = {}


class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
       
        if isinstance(obj.__class__, DeclarativeMeta) or type(obj) is  datetime:
            fields = {}          
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata' ]:
                data = obj.__getattribute__(field)
                try:
                    if isinstance(data, (datetime,datetime.date)):
                        data =  obj.isoformat()
                    json.dumps(data) 
                    fields[field] = data
                    
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields
        return json.JSONEncoder.default(self, obj)




def action(func):
    func.__name__ = f"comments_{func.__name__}"
    _actions[func.__name__] = func
    return func

def get_actions():
    return _actions.copy()


@action
@validate(schema.thread_create)
def thread_create(context, data_dict):
    """Create a thread for the subject.

    Args:
        subject_id(str): unique ID of the commented entity
        subject_type(str:package|resource|user|group): type of the commented entity

    """
    _check_blocked(data_dict)

    thread = Thread.for_subject(
        data_dict["subject_type"], data_dict["subject_id"], init_missing=True
    )

    if thread.id:
        raise tk.ValidationError(
            {"id": ["Thread for the given subject_id and subject_type already exists"]}
        )
    if thread.get_subject() is None:
        raise tk.ObjectNotFound("Cannot find subject for thread")

    context["session"].add(thread)
    context["session"].commit()
    thread_dict = get_dictizer(type(thread))(thread, context)
    return thread_dict


@action
@validate(schema.thread_show)
def thread_show(context, data_dict):
    """Show the subject's thread.

    Args:
        subject_id(str): unique ID of the commented entity
        subject_type(str:package|resource|user|group): type of the commented entity
        init_missing(bool, optional): return an empty thread instead of 404
        include_comments(bool, optional): show comments from the thread
        include_author(bool, optional): show authors of the comments
        combine_comments(bool, optional): combine comments into a tree-structure
        after_date(str:ISO date, optional): show comments only since the given date
    """
    tk.check_access("comments_thread_show", context, data_dict)
    thread = Thread.for_subject(
        data_dict["subject_type"],
        data_dict["subject_id"],
        init_missing=data_dict["init_missing"],
    )
    if thread is None:
        raise tk.ObjectNotFound("Thread not found")

    context["include_comments"] = data_dict["include_comments"]
    context["combine_comments"] = data_dict["combine_comments"]
    context["include_author"] = data_dict["include_author"]
    context["after_date"] = data_dict.get("after_date")

    context["newest_first"] = data_dict["newest_first"]

    thread_dict = get_dictizer(type(thread))(thread, context)
    return thread_dict


@action
@validate(schema.thread_delete)
def thread_delete(context, data_dict):
    """Delete the thread.

    Args:
        id(str): ID of the thread
    """
    tk.check_access("comments_thread_delete", context, data_dict)
    thread = (
        context["session"]
        .query(Thread)
        .filter(Thread.id == data_dict["id"])
        .one_or_none()
    )
    if thread is None:
        raise tk.ObjectNotFound("Thread not found")

    context["session"].delete(thread)
    context["session"].commit()
    thread_dict = get_dictizer(type(thread))(thread, context)
    return thread_dict


@action
@validate(schema.comment_create)
def comment_create(context, data_dict):
    """Add a comment to the thread.

    Args:
        subject_id(str): unique ID of the commented entity
        subject_type(str:package|resource|user|group): type of the commented entity
        content(str): comment's message
        reply_to_id(str, optional): reply to the existing comment
        create_thread(bool, optional): create a new thread if it doesn't exist yet
    """
    _check_blocked(data_dict)
    
    thread_data = {
        "subject_id": data_dict["subject_id"],
        "subject_type": data_dict["subject_type"],
    }
    try:
        thread_dict = tk.get_action("comments_thread_show")(context.copy(), thread_data)
    except tk.ObjectNotFound:
        if not data_dict["create_thread"]:
            raise
        try:
            thread_dict = tk.get_action("comments_thread_create")(
                context.copy(), thread_data
            )
        except Exception as e:
            log.error("Ocurrió un error al crear el hilo de comentarios: {e}")    

    author_id = data_dict.get("author_id")
    email_comment = data_dict["email"]
    
    if context.get("auth_user_obj") is not None:
        can_set_author_id = context.get("ignore_auth") or context["auth_user_obj"].sysadmin
    else:
        can_set_author_id = context.get("ignore_auth")

   
    if not email_comment:
        email_comment  = context["auth_user_obj"].email

    if not author_id or not can_set_author_id:
        author_id = context["user"]
       
    
    reply_to_id = data_dict.get("reply_to_id")
    
    if reply_to_id:
        parent = tk.get_action("comments_comment_show")(
            context.copy(), {"id": reply_to_id}
        )
        if parent["thread_id"] != thread_dict["id"]:
            raise tk.ValidationError(
                {"reply_to_id": ["Coment is owned by different thread"]}
            )
    comment = Comment(
        thread_id=thread_dict["id"],
        content=data_dict["content"],
        author_type=data_dict["author_type"],
        extras=data_dict["extras"],
        email=email_comment,
        username = data_dict["username"],
        consent = data_dict["consent"],
        author_id=author_id,
        reply_to_id=reply_to_id,
    )
    try:
        author = comment.get_author()
    except Exception as e:
        log.error(f"Ocurrió un error al obtener el autor del comentario: {e}")

    if author is not None:
        comment.author_id = author.id
    
    try:
        approve_comment_by_role(author,comment,data_dict)

    except Exception as e:
        log.error(f"Ocurrió un error al obtener si el comentario será aprobado automaticamente: {e}")
    
    
    context["session"].add(comment)
    context["session"].commit()
    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.created.send(comment.thread_id, comment=comment_dict)

    try:
        generate_send_user_mail( author,data_dict)
    except Exception as e:
        log.error(f"Ocurrió un error al enviar el correo electrónico al usuario: {e}")
    try:
        generate_send_organism_mail(comment_dict, data_dict)
    except Exception as e:
        log.error(f"Ocurrió un error al enviar el correo electrónico al organismo: {e}")
    return comment_dict


def get_all_comments_ckan_from_package():
    
    comments_with_title = model.Session.query(
        Comment, model.Package
    ).join(
        Thread, Comment.thread_id == Thread.id
    ).join(
        model.Package, Thread.subject_id == model.Package.id
    ).filter(
        Thread.subject_type == 'package'
    ).all()

    salida= flatten_join_prefix(comments_with_title)
    
    return json.dumps({"data":salida}, cls=AlchemyEncoder)
 

def get_all_comments_ckan_from_package_by_user(ckan_user_id):
    
    comments_with_title = model.Session.query(
        Comment, model.Package
    ).join(
        Thread, Comment.thread_id == Thread.id
    ).join(
        model.Package, Thread.subject_id == model.Package.id
    ).join(
        model.Group, model.Package.owner_org == model.Group.id
    ).join(
        model.Member, model.Group.id == model.Member.group_id
    ).join(
        model.User, model.Member.table_id == ckan_user_id
    ).filter(
        Thread.subject_type == 'package',
        model.Package.state == 'active',
        model.Member.state == 'active'
    ).all()

    salida= flatten_join_prefix(comments_with_title)
    
    return json.dumps({"data":salida}, cls=AlchemyEncoder)
       
def approve_comment_by_role(author,comment,data_dict):
    
    if author is not None:
           
            rows = get_roles_by_author_id(author)
            
            for row in rows:
                if row.role == ROLE_ADMINISTRATOR or row.role == ROLE_APORTA:
                    comment.approve()
                    break
                if row.role == ROLE_PUBLICADOR and user_belong_to_same_organization(author,data_dict):
                    comment.approve()

def user_belong_to_same_organization( author, data_dict):
    email_belong_to = False

    user_author = model.User.get(author.id)
    email_commenting_user = user_author.email

    package = model.Package.get(data_dict["subject_id"])
    members = toolkit.get_action('member_list')(
        data_dict={'id': package.owner_org, 'table_name': 'user', 'capacity': 'editor', 'state': 'active'})

    for member in members:
        user = model.User.get(member[0])
        if user.email == email_commenting_user:
            email_belong_to = True 
    
    return email_belong_to



def generate_send_user_mail(  author,data_dict):

    if author is None:
        addressee = data_dict["email"]
    else: 
        addressee = author.email
    
    subject = conf.get('ckanext.comments.email.subject.send_mail_user')
    path = conf.get('ckanext.comments.template.emails') 
    url = conf.get('ckanext.comments.url.images.drupal')
    url_logos = conf.get('ckanext.comments.url.image.logos')
    url_image_subscribe = conf.get('ckanext.comments.url.image.subscribe')
    url_subscribe = conf.get('ckanext.comments.url.subscribe')
    env =  Environment(loader=FileSystemLoader(path))
    
 
    template_usuario = env.get_template('email_usuario.html')
 
    body = template_usuario.render(url=url, url_logos=url_logos, url_image_subscribe=url_image_subscribe, url_subscribe=url_subscribe, email=addressee, mensaje=data_dict["content"] )
    if addressee:
        msg = MIMEMultipart()
        msg['From'] = conf.get('smtp.mail_from')
        msg['To'] = addressee
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        send_email(addressee, msg)
    

def generate_send_organism_mail(comment, data_dict):

    package = model.Package.get(data_dict["subject_id"])
    members = toolkit.get_action('member_list')(
         data_dict={'id':  package.owner_org, 'table_name': 'user', 'capacity': 'editor', 'state': 'active'})
   
    mail_to = []
    for member in members:
        user = model.User.get(member[0])
        if user and  user.state == 'active' and user.email and len(user.email) > 0:
            mail_to.append(user.email)

    subject = conf.get('ckanext.comments.email.subject.send_mail_organismo') 
    path = conf.get('ckanext.comments.template.emails') 
    url = conf.get('ckanext.comments.url.images.drupal')
    url_logos = conf.get('ckanext.comments.url.image.logos')
    url_image_subscribe = conf.get('ckanext.comments.url.image.subscribe')
    url_subscribe = conf.get('ckanext.comments.url.subscribe')
    node_title = package.title
    comment_created = h.render_datetime(comment['created_at'])
    comment_name = comment['username']
    comment_email = comment['email']
    comment_content= comment['content']

    url_name = conf.get('ckan.site_url')+'/es/catalogo/'+package.name
    email_from = conf.get('smtp.mail_from')
    env =  Environment(loader=FileSystemLoader(path))
    template_organismo = env.get_template('email_organismo.html')
 
    body = template_organismo.render(url=url, url_name=url_name, url_logos=url_logos, url_image_subscribe=url_image_subscribe, url_subscribe=url_subscribe, node_title=node_title, comment_created=comment_created,comment_name=comment_name,comment_email=comment_email,comment_content=comment_content )

    if mail_to:
        addressees = ', '.join(mail_to)
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = addressees
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))
        send_email(mail_to, msg)



def send_email( addressees, msg):
    from socket import error as socket_error

    if addressees and msg:

        smtp_connection = smtplib.SMTP()
        smtp_server = conf.get('smtp.server', '')
        smtp_starttls = False
        smtp_user = conf.get('smtp.user')
        smtp_password = conf.get('smtp.password')
        try:
            
            smtp_connection.connect(smtp_server)
            smtp_connection.ehlo()


            if smtp_starttls:
                if smtp_connection.has_extn('STARTTLS'):
                    smtp_connection.starttls()
                    smtp_connection.ehlo()
                else:
                    raise MailerException("SMTP server does not support STARTTLS")

            if smtp_user:
                assert smtp_password, ("If smtp.user is configured then "
                                        "smtp.password must be configured as well.")
                smtp_connection.login(smtp_user, smtp_password)
            email_from = conf.get('smtp.mail_from')
            smtp_connection.sendmail(email_from,addressees, msg.as_string())
            smtp_connection.quit()
          

        except smtplib.SMTPException as e:
            msg = '%r' % e
            log.exception(msg)
            raise MailerException(msg)
        except AttributeError as e:
            msg = '%r' % e
            log.exception(msg)
            raise MailerException(msg)
        except socket_error as e:
            log.exception(e)
            raise MailerException(e)
    else:
        log.info("Skip sending email. addressees ({0})  aren't correct".format(addressees))





@action
@validate(schema.comment_show)
def comment_show(context, data_dict):
   
    """Show the details of the comment

    Args:
        id(str): ID of the comment
    """
    tk.check_access("comments_comment_show", context, data_dict)
    comment = (
        context["session"]
        .query(Comment)
        .filter(Comment.id == data_dict["id"])
        .one_or_none()
    )
    if comment is None:
        raise tk.ObjectNotFound("Comment not found")
    comment_dict = get_dictizer(type(comment))(comment, context)
    return comment_dict


@action
@validate(schema.comment_approve)
def comment_approve(context, data_dict):
    """Approve draft comment

    Args:
        id(str): ID of the comment
    """
    tk.check_access("comments_comment_approve", context, data_dict)
    comment = (
        context["session"]
        .query(Comment)
        .filter(Comment.id == data_dict["id"])
        .one_or_none()
    )
    if comment is None:
        raise tk.ObjectNotFound("Comment not found")
    comment.approve()
    context["session"].commit()

    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.approved.send(comment.thread_id, comment=comment_dict)

    package_info_string=get_package_info(comment_dict)
    package_info = json.loads(package_info_string)
    try:
        send_email_comment_approved( comment_dict,package_info[0])
    except Exception as e:
            log.error("Ocurrió un error al enviar el email de aprobación: {e}") 
    return comment_dict





def get_package_info (comment):
    comments_with_title = model.Session.query(
        model.Package
    ).join(
        Thread, model.Package.id == Thread.subject_id
    ).filter(
        Thread.id == comment['thread_id']
    ).all()

    serialized_results = [serialize(c) for c in comments_with_title]
    
    return json.dumps(serialized_results, cls=AlchemyEncoder)
    


def send_email_comment_approved(comment,package_info):
    username = None
    if comment['username']:
        username =comment['username']
    else:
        username =comment['email']
    
    subject_init = conf.get('ckanext.comments.email.subject.comment_approved_init')
    subject_end = conf.get('ckan.site_title')
    subject = subject_init
    path = conf.get('ckanext.comments.template.emails') 
    url = conf.get('ckanext.comments.url.images.drupal')
    url_logos = conf.get('ckanext.comments.url.image.logos')
    url_image_subscribe = conf.get('ckanext.comments.url.image.subscribe')
    url_subscribe = conf.get('ckanext.comments.url.subscribe')
    url_name = conf.get('ckan.site_url')+'/es/catalogo/'+package_info['name']
    env =  Environment(loader=FileSystemLoader(path))
    
 
    template_usuario = env.get_template('email_comment_approved.html')
 
    body = template_usuario.render(url=url,url_name=url_name, url_logos=url_logos, url_image_subscribe=url_image_subscribe, url_subscribe=url_subscribe, username=username,title=package_info['title'],email=comment['email'], mensaje=comment['content'], subject_end=subject_end )
    if comment['email']:
        msg = MIMEMultipart()
        msg['From'] = conf.get('smtp.mail_from')
        msg['To'] = comment['email']
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        send_email(comment['email'], msg)    


def send_email_comment_deleted(  comment,data_dict):
    
    
    subject = data_dict['__extras']['subject']
    path = conf.get('ckanext.comments.template.emails') 
    url = conf.get('ckanext.comments.url.images.drupal')
    url_logos = conf.get('ckanext.comments.url.image.logos')
    url_image_subscribe = conf.get('ckanext.comments.url.image.subscribe')
    url_subscribe = conf.get('ckanext.comments.url.subscribe')
    env =  Environment(loader=FileSystemLoader(path))
    
 
    template_usuario = env.get_template('email_comment_deleted.html')
 
    body = template_usuario.render(url=url, url_logos=url_logos, url_image_subscribe=url_image_subscribe, url_subscribe=url_subscribe, body=data_dict['__extras']['body'] )
    if comment['email']:
        msg = MIMEMultipart()
        msg['From'] = conf.get('smtp.mail_from')
        msg['To'] = comment['email']
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        send_email(comment['email'], msg)           

@action
@validate(schema.comment_draft)
def comment_draft(context, data_dict):
    """Put comment in state draft 

    Args:
        id(str): ID of the comment
    """
    tk.check_access("comments_comment_draft", context, data_dict)
    comment = (
        context["session"]
        .query(Comment)
        .filter(Comment.id == data_dict["id"])
        .one_or_none()
    )
    if comment is None:
        raise tk.ObjectNotFound("Comment not found")
    comment.draft()
    context["session"].commit()

    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.updated.send(comment.thread_id, comment=comment_dict)
    
    return comment_dict


@action
@validate(schema.comment_delete)
def comment_delete(context, data_dict):

    """Remove existing comment

    Args:
        id(str): ID of the comment
    """
    tk.check_access("comments_comment_delete", context, data_dict)
    comment = (
        context["session"]
        .query(Comment)
        .filter(Comment.id == data_dict["id"])
        .one_or_none()
    )
    if comment is None:
        raise tk.ObjectNotFound("Comment not found")

    context["session"].delete(comment)
    context["session"].commit()
    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.deleted.send(comment.thread_id, comment=comment_dict)
    if(len(data_dict['__extras']['subject']) != 0 and len(data_dict['__extras']['body']) != 0 ):
        try:
            send_email_comment_deleted(comment_dict,data_dict)
        except Exception as e:
            log.error("Ocurrió un error al enviar el email de borrado: {e}") 
    return comment_dict


@action
@validate(schema.comment_update)
def comment_update(context, data_dict):
    """Update existing comment

    Args:
        id(str): ID of the comment
        content(str): comment's message
    """

    tk.check_access("comments_comment_update", context, data_dict)
    comment = (
        context["session"]
        .query(Comment)
        .filter(Comment.id == data_dict["id"])
        .one_or_none()
    )

    if comment is None:
        raise tk.ObjectNotFound("Comment not found")

    comment.content = data_dict["content"]
    comment.modified_at = datetime.utcnow()
    context["session"].commit()
    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.updated.send(comment.thread_id, comment=comment_dict)
    return comment_dict


@action
@validate(schema.blocked_entity_create)
def blocked_entity_create(context, data_dict):
    """Block the entity so that it cannot be commented on

    Args:
        subject_id(str): unique ID of the entity
        subject_type(str:package|resource|user|group): type of the entity

    """
    tk.check_access("comments_blocked_entity_create", context, data_dict)
    subject_type = data_dict["subject_type"]
    subject_id = data_dict["subject_id"]
    blocked_entity_dict = None
    try:
        blocked_entity = blocked_entity_show(context, data_dict)
        log.info(f'[blocked_entity_create] The {subject_type} with ID {subject_id} already has comments blocked.')
    except tk.ObjectNotFound:
        blocked_entity = BlockedEntity()
        blocked_entity.subject_id = subject_id
        blocked_entity.subject_type = subject_type
        context["session"].add(blocked_entity)
        context["session"].commit()
        log.info(f'[blocked_entity_create] Blocked comments for {subject_type} with ID {subject_id}.')
    blocked_entity_dict = get_dictizer(type(blocked_entity))(blocked_entity, context)
    return blocked_entity_dict


@action
@validate(schema.blocked_entity_delete)
def blocked_entity_delete(context, data_dict):
    """Unblock the entity so that it can be commented again.

    Args:
        subject_id(str): unique ID of the commented entity
        subject_type(str:package|resource|user|group): type of the commented entity

    """
    tk.check_access("comments_blocked_entity_delete", context, data_dict)
    subject_type = data_dict["subject_type"]
    subject_id = data_dict["subject_id"]
    blocked_entity_dict = None
    blocked_entity = BlockedEntity.for_subject(subject_type, subject_id)
    if blocked_entity:
        context["session"].delete(blocked_entity)
        context["session"].commit()
        log.info(f'[blocked_entity_delete] Unblocked comments for {subject_type} with ID {subject_id}.')
        blocked_entity_dict = get_dictizer(type(blocked_entity))(blocked_entity, context)
    else:
        log.info(f'[blocked_entity_delete] The {subject_type} with ID {subject_id} does NOT have comments blocked.')
    return blocked_entity_dict

@action
@validate(schema.blocked_entity_show)
def blocked_entity_show(context, data_dict):
    """Show the details of the blocked entity

    Args:
        subject_id(str): unique ID of the entity
        subject_type(str:package|resource|user|group): type of the entity
    """
    tk.check_access("comments_blocked_entity_show", context, data_dict)
    subject_type = data_dict["subject_type"]
    subject_id = data_dict["subject_id"]
    blocked_entity = BlockedEntity.for_subject(subject_type, subject_id)
    if blocked_entity is None:
        log.info(f'[blocked_entity_show] The {subject_type} with ID {subject_id} does NOT have comments blocked.')
        raise tk.ObjectNotFound("BlockedEntity not found")
    log.debug(f'[blocked_entity_show] The {subject_type} with ID {subject_id} has comments blocked.')
    return get_dictizer(type(blocked_entity))(blocked_entity, context)

def _check_blocked(data_dict):
    subject_id = data_dict["subject_id"]
    subject_type = data_dict["subject_type"]
    if is_a_blocked_entity(subject_id, subject_type):
        log.info(f'[_check_blocked] The {subject_type} with ID {subject_id} has comments blocked.')
        raise tk.ValidationError({"subject": [_('The message was not sent because the entity has messages disabled.')]})

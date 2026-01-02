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

from typing import Any, Callable, Optional

from werkzeug.utils import import_string

import ckan.plugins.toolkit as tk

CONFIG_REQUIRE_APPROVAL = "ckanext.comments.require_approval"
DEFAULT_REQUIRE_APPROVAL = True

CONFIG_DRAFT_EDITS = "ckanext.comments.draft_edits"
DEFAULT_DRAFT_EDITS = True

CONFIG_DRAFT_EDITS_BY_AUTHOR = "ckanext.comments.draft_edits_by_author"
DEFAULT_DRAFT_EDITS_BY_AUTHOR = True

CONFIG_APPROVED_EDITS = "ckanext.comments.approved_edits"
DEFAULT_APPROVED_EDITS = False

CONFIG_APPROVED_EDITS_BY_AUTHOR = "ckanext.comments.approved_edits_by_author"
DEFAULT_APPROVED_EDITS_BY_AUTHOR = False

CONFIG_MOBILE_THRESHOLD = "ckanext.comments.mobile_depth_threshold"
DEFAULT_MOBILE_THRESHOLD = 3

CONFIG_MODERATOR_CHECKER = "ckanext.comments.moderator_checker"
DEFAULT_MODERATOR_CHECKER = "ckanext.comments.utils:comments_is_moderator"

CONFIG_ENABLE_DATASET = "ckanext.comments.enable_default_dataset_comments"
DEFAULT_ENABLE_DATASET = False


def approval_required() -> bool:
    return tk.asbool(tk.config.get(CONFIG_REQUIRE_APPROVAL, DEFAULT_REQUIRE_APPROVAL))


def allow_draft_edits() -> bool:
    return tk.asbool(
        tk.config.get(
            CONFIG_DRAFT_EDITS,
            DEFAULT_DRAFT_EDITS,
        )
    )


def allow_draft_edits_by_author() -> bool:
    return tk.asbool(
        tk.config.get(
            CONFIG_DRAFT_EDITS,
            DEFAULT_DRAFT_EDITS_BY_AUTHOR,
        )
    )


def allow_approved_edits() -> bool:
    return tk.asbool(
        tk.config.get(
            CONFIG_APPROVED_EDITS,
            DEFAULT_APPROVED_EDITS,
        )
    )


def allow_approved_edits_by_author() -> bool:
    return tk.asbool(
        tk.config.get(
            CONFIG_DRAFT_EDITS,
            DEFAULT_APPROVED_EDITS_BY_AUTHOR,
        )
    )


def mobile_depth_threshold() -> int:
    return tk.asint(tk.config.get(CONFIG_MOBILE_THRESHOLD, DEFAULT_MOBILE_THRESHOLD))


def use_default_dataset_comments() -> bool:
    return tk.asbool(tk.config.get(CONFIG_ENABLE_DATASET, DEFAULT_ENABLE_DATASET))


def moderator_checker() -> Optional[Callable[[Any, Any, Any], bool]]:
    checker = tk.config.get(CONFIG_MODERATOR_CHECKER, DEFAULT_MODERATOR_CHECKER)
    return import_string(checker, silent=True)

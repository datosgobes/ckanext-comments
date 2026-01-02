/*
* Copyright (C) 2025 Entidad Pública Empresarial Red.es
*
* This file is part of "comments (datos.gob.es)".
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 2 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program. If not, see <http://www.gnu.org/licenses/>.
*/

ckan.module("comments-thread", function ($) {
  "use strict";

  return {
    options: {
      subjectId: null,
      subjectType: null,
      ajaxReload: null,
    },
    initialize: function () {
      $.proxyAll(this, /_on/);
      this.$(".comment-actions .remove-comment").on(
        "click",
        this._onRemoveComment
      );
      this.$(".comment-actions .approve-comment").on(
        "click",
        this._onApproveComment
      );
      this.$(".comment-actions .draft-comment").on(
        "click",
        this._onDraftComment
      );
      this.$(".comment-actions .reply-to-comment").on(
        "click",
        this._onReplyToComment
      );
      this.$(".comment-actions .edit-comment").on("click", this._onEditComment);
      this.$(".comment-actions .save-comment").on("click", this._onSaveComment);
      this.$(".comment-footer").on("click", this._onFooterClick);
      this.$(".comment-form").off("submit").on("submit", this._onSubmit);
      this.$("#block_comments").on("click", this._onBlockComments);
      this.$("#unblock_comments").on("click", this._onUnblockComments);

    },
    teardown: function () {
      this.$(".comment-action.remove-comment").off(
        "click",
        this._onRemoveComment
      );
      this.$(".comment-actions .approve-comment").off(
        "click",
        this._onApproveComment
      );
      this.$(".comment-actions .draft-comment").off(
        "click",
        this._onDraftComment
      );

      this.$(".comment-form").off("submit", this._onSubmit);
    },
    _onFooterClick: function (e) {
      if (e.target.classList.contains("cancel-reply")) {
        this._disableActiveReply();
      } else if (e.target.classList.contains("save-reply")) {
        var content = e.currentTarget.querySelector(
          ".reply-textarea-wrapper textarea"
        ).value;
        this._saveComment({
          content: content,
          reply_to_id: e.target.dataset.id,
        });
      }
    },
    _onRemoveComment: function (e) {
      
      var id = e.currentTarget.dataset.id;

      var subject = $('#confirmation-modal-'+id + ' #edit-email-subject').val();
      var body = $('#confirmation-modal-'+id + ' .form-textarea-wrapper textarea').val();

      var ajaxReload = this.options.ajaxReload;

      this.sandbox.client.call(
        "POST",
        "comments_comment_delete",
        {
          id: id,
          subject: subject,
          body: body
        },
        function (e) {
            if (ajaxReload) {
                $(".modal").modal("hide");

                $(document).trigger("comments:changed");
            } else {
                window.location.reload();
            }
        }
      );
    },
    _onApproveComment: function (e) {
      var id = e.currentTarget.dataset.id;
      var ajaxReload = this.options.ajaxReload;

      this.sandbox.client.call(
        "POST",
        "comments_comment_approve",
        {
          id: id,
        },
        function () {
            if (ajaxReload) {
                $(document).trigger("comments:changed");
            } else {
                window.location.reload();
            }
        }
      );
    },
    _onDraftComment: function (e) {
      var id = e.currentTarget.dataset.id;
      var ajaxReload = this.options.ajaxReload;

      this.sandbox.client.call(
        "POST",
        "comments_comment_draft",
        {
          id: id,
        },
        function () {
            if (ajaxReload) {
                $(document).trigger("comments:changed");
            } else {
                window.location.reload();
            }
        }
      );
    },
    _disableActiveReply: function () {
      $(".comment .reply-textarea-wrapper").remove();
    },
    _onReplyToComment: function (e) {
      this._disableActiveReply();
      this._disableActiveEdit();
      var id = e.currentTarget.dataset.id;
      var comment = $(e.currentTarget).closest(".comment");
      var textarea = $('<textarea rows="5" class="form-control">');
      comment.find(".comment-footer").append(
        $('<div class="control-full reply-textarea-wrapper">').append(
          textarea,
          $("<div>")
            .addClass("reply-actions")
            .append(
              $("<button>", { text: this._("Reply"), "data-id": id }).addClass(
                "btn btn-default reply-action save-reply"
              ),
              $("<button>", { text: this._("Cancel") }).addClass(
                "btn btn-danger reply-action cancel-reply"
              )
            )
        )
      );
    },
    _disableActiveEdit: function () {
      $(".comment.edit-in-progress")
        .removeClass(".edit-in-progress")
        .find(".comment-action.save-comment")
        .addClass("hidden")
        .prevObject.find(".comment-action.edit-comment")
        .removeClass("hidden")
        .prevObject.find(".edit-textarea-wrapper")
        .remove()
        .prevObject.find(".comment-content")
        .removeClass("hidden");
    },
    _onEditComment: function (e) {
      this._disableActiveReply();
      this._disableActiveEdit();
      var target = $(e.currentTarget).addClass("hidden");
      target.parent().find(".save-comment").removeClass("hidden");
      $('.btn.btn-secondary.button--link').show();
      $('.form.comment-form').hide();
      var content = target
        .closest(".comment")
        .addClass("edit-in-progress")
        .find(".comment-content")
        .not("form[id^='formNewComment'] .comment-content");;

      var commentText = content.contents().filter(function() {
        return this.nodeType === 3;
      }).text().trim();

      var textarea = $('<textarea rows="5" class="form-control">');
      textarea.text(commentText);
      content
        .addClass("hidden")
        .parent()
        .append(
          $('<div class="control-full edit-textarea-wrapper mt-4">').append(textarea)
        );
    },
    _onSaveComment: function (e) {
      var self = this;
      var id = e.currentTarget.dataset.id;
      var target = $(e.currentTarget);
      var notify = this.sandbox.notify;
      var _ = this.sandbox.translate;
      var content = target.closest(".comment").find(".comment-body .edit-textarea-wrapper textarea").filter(':visible');
      var ajaxReload = this.options.ajaxReload;

      this.sandbox.client.call(
        "POST",
        "comments_comment_update",
        {
          id: id,
          content: content.val(),
        },
        function () {
            if (ajaxReload) {
                $(document).trigger("comments:changed");
            } else {
                window.location.reload();
            }
        },
        function (err) {
          console.log(err);
          var oldEl = notify.el;
          notify.el = target.closest(".comment");
          notify(
            self._("An Error Occurred").fetch(),
            self._("Comment cannot be updated").fetch(),
            "error"
          );
          notify.el.find(".alert .close").attr("data-dismiss", "alert");
          notify.el = oldEl;
        }
      );
    },
    _onSubmit: function (e) {
      e.preventDefault();
      var data = new FormData(e.target);
      this._saveComment({ content: data.get("content") ,consent: data.get('consent'),email: data.get("email"), username: data.get("username") , create_thread: true, url: data.get('url'),
      reply_to_id: e.target.dataset.id, successful_success_message: data.get('successful-sending-message')});      
    },
    _saveComment: function (data) {
      data.subject_id = this.options.subjectId;
      data.subject_type = this.options.subjectType;
      var ajaxReload = this.options.ajaxReload;
      var success_message = data.successful_success_message

      this.sandbox.client.call(
        "POST",
        "comments_comment_create",
        data,
        function () {
          $('.form-group.control-full .btn.btn-primary').prop('disabled' , false);
            if (ajaxReload) {
              $(document).trigger("comments:changed");
            } else {
              if (success_message) {
                localStorage.setItem("successful_sending_comment", success_message)
                localStorage.setItem("successful_sending_comment_category", "alert-success");
              }
              $('form.comment-form').trigger("reset");
              window.location.href = window.location.pathname;
            }
        },
        function (err) {
          if (err && err.responseJSON && err.responseJSON.error) {
            const errors = err.responseJSON.error;
            const first_key_error = Object.keys(errors)[0];
            const first_error_message = errors[first_key_error];
            if (first_key_error == "subject" && first_error_message){
              localStorage.setItem("unsuccessful_sending_comment", first_error_message)
              localStorage.setItem("unsuccessful_sending_comment_category", "alert-error");
              $('form.comment-form').trigger("reset");
              window.location.href = window.location.pathname;
            }else{
              $('.form-group.control-full .btn.btn-primary').prop('disabled' , false);
              $('.form-group').removeClass("error");
              $('.form-group.comment-'+Object.keys(err.responseJSON.error)[0]).addClass("error");
            }
          }
        }
      );
    },
    _onBlockComments: function (e) {
      var subject_id = this.options.subjectId;
      var subject_type = this.options.subjectType;
      this.sandbox.client.call(
        "POST",
        "comments_blocked_entity_create",
        {
          subject_id: subject_id,subject_type:subject_type
        },
        function () {
            window.location.reload();
        }
      );
    },
    _onUnblockComments: function (e) {
      var subject_id = this.options.subjectId;
      var subject_type = this.options.subjectType;
      this.sandbox.client.call(
        "POST",
        "comments_blocked_entity_delete",
        {
          subject_id: subject_id,subject_type:subject_type
        },
        function () {
            window.location.reload();
        }
      );
    },
  };
});

$('#addNewComment').on('click', function(e) {
  e.preventDefault();
const $target = $('#formNewComment');
  if ($target.length) {
    $target.show();

    $('html, body').animate({
      scrollTop: $target.offset().top
    }, 600, function() {
    });
  }
});

var btns = document.querySelectorAll('[id^="addNewComment"]');

var forms = document.querySelectorAll('[id^="formNewComment"]');


btns.forEach(function(btn) {
  btn.addEventListener("click", function() {
    var parts = btn.id.split('_');
    var suffix = parts.length > 1 ? parts[1] : '';

    var formId = "formNewComment" + (suffix ? '_' + suffix : '');
    var form = document.getElementById(formId);

    forms.forEach(function(otherForm) {

      $(".comment.edit-in-progress")
      .removeClass(".edit-in-progress")
      .find(".comment-action.save-comment")
      .addClass("hidden")
      .prevObject.find(".comment-action.edit-comment")
      .removeClass("hidden")
      .prevObject.find(".edit-textarea-wrapper")
      .remove()
      .prevObject.find(".comment-content")
      .removeClass("hidden"); 

      if (otherForm.style.display === "block") {
        otherForm.style.display = "none";
        document.getElementById('addNewComment').style.display = "block";

        var otherBtn = document.getElementById('addNewComment_' + otherForm.dataset.id);
        if (otherBtn) {
          otherBtn.style.display = "inline";
        }
      }
    });

    form.style.display = "block";
    btn.style.display = "none";
  });
});

forms.forEach(function(form) {

  form.addEventListener("submit", function() {
    var submitButton = form.querySelector('button[type="submit"]');

    submitButton.disabled = true;

  });
});


$("div[id^='confirmation-modal-']").on('click', function() {
  var id = this.id;
  
  if($('#'+id+' .send-email-notification').is(":checked")) {
    
    $('#'+id +' .email-notification-deleted').css('display', 'block');
} else {
 
  $('#'+id +' .email-notification-deleted').css('display', 'none');
}
});


window.addEventListener("DOMContentLoaded", () => {
  const unsuccessful_msg = localStorage.getItem("unsuccessful_sending_comment");
  const unsuccessful_category = localStorage.getItem("unsuccessful_sending_comment_category") || "alert-error";

  if (unsuccessful_msg) {
    const div = document.createElement("div");
    div.className = 'alert fade in ' + unsuccessful_category;
    div.innerHTML = unsuccessful_msg;
    document.querySelector(".flash-messages")?.appendChild(div);

    localStorage.removeItem("unsuccessful_sending_comment");
    localStorage.removeItem("unsuccessful_sending_comment_category");
  }

  const successful_msg = localStorage.getItem("successful_sending_comment");
  const successful_category = localStorage.getItem("successful_sending_comment_category") || "alert-info";

  if (successful_msg) {
    const div = document.createElement("div");
    div.className = 'alert fade in ' + successful_category;
    div.innerHTML = successful_msg;
    document.querySelector(".flash-messages")?.appendChild(div);

    localStorage.removeItem("successful_sending_comment");
    localStorage.removeItem("successful_sending_comment_category");
  }
});
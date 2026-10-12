import uuid

from django.conf import settings
from django.db import models


class Document(models.Model):
    """A rich-text document owned by one user and shareable with others.

    Content is stored as sanitized HTML (see ``documents.sanitize``). HTML was
    chosen over ProseMirror JSON because it round-trips cleanly with TipTap
    (``editor.getHTML()`` / ``content``) and with the Markdown/plain-text import
    path, keeping one representation across create, edit and import.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, default="Untitled document")
    content = models.TextField(blank=True, default="")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_documents",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Role returned for the document's owner (Share.Role covers viewer/editor).
    OWNER_ROLE = "owner"

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.owner})"

    # --- Access helpers ---------------------------------------------------
    def share_for(self, user):
        """Return the Share row for ``user``, or None."""
        if not user or not getattr(user, "is_authenticated", False):
            return None
        return self.shares.filter(user=user).first()

    def role_for(self, user):
        """Return 'owner' | 'editor' | 'viewer' | None for ``user``."""
        if self.owner_id == getattr(user, "id", None):
            return self.OWNER_ROLE
        share = self.share_for(user)
        return share.role if share else None

    def can_view(self, user) -> bool:
        return self.role_for(user) is not None

    def can_edit(self, user) -> bool:
        return self.role_for(user) in {self.OWNER_ROLE, Share.Role.EDITOR}


class Share(models.Model):
    """Grants one user access to one document with a role (viewer/editor)."""

    class Role(models.TextChoices):
        VIEWER = "viewer", "Viewer (read-only)"
        EDITOR = "editor", "Editor (can edit)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="shares"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shared_documents",
    )
    role = models.CharField(
        max_length=10, choices=Role.choices, default=Role.VIEWER
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="shares_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A user can hold at most one role per document.
        constraints = [
            models.UniqueConstraint(
                fields=["document", "user"], name="unique_share_per_user_document"
            )
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.document.title} -> {self.user} ({self.role})"

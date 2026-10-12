from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Document, Share
from .sanitize import sanitize_html

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class ShareSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Share
        fields = ["id", "user", "role", "created_at"]


class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight representation for the document list (no heavy content)."""

    owner = UserSerializer(read_only=True)
    role = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    shared_count = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id", "title", "owner", "role", "is_owner",
            "shared_count", "created_at", "updated_at",
        ]

    def get_role(self, obj) -> str:
        return obj.role_for(self.context["request"].user)

    def get_is_owner(self, obj) -> bool:
        return obj.owner_id == self.context["request"].user.id

    def get_shared_count(self, obj) -> int:
        # Uses prefetched shares when available to avoid N+1 queries.
        return len(obj.shares.all())


class DocumentDetailSerializer(DocumentListSerializer):
    """Full document including sanitized content and the share list."""

    shares = ShareSerializer(many=True, read_only=True)

    class Meta(DocumentListSerializer.Meta):
        fields = DocumentListSerializer.Meta.fields + ["content", "shares"]

    def validate_title(self, value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Title cannot be empty.")
        if len(value) > 255:
            raise serializers.ValidationError("Title is too long (max 255).")
        return value

    def validate_content(self, value: str) -> str:
        # Sanitize on the way in so stored content is always safe to render.
        return sanitize_html(value or "")


class ShareCreateSerializer(serializers.Serializer):
    """Input for granting access: share by email with a role."""

    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=Share.Role.choices, default=Share.Role.VIEWER
    )

    def validate_email(self, value: str) -> str:
        return value.strip().lower()

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (
    action,
    api_view,
    permission_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .importers import SUPPORTED_EXTENSIONS, ImportError_, import_file
from .models import Document, Share
from .permissions import DocumentAccessPermission
from .serializers import (
    DocumentDetailSerializer,
    DocumentListSerializer,
    ShareCreateSerializer,
    ShareSerializer,
    UserSerializer,
)

User = get_user_model()


class DocumentViewSet(viewsets.ModelViewSet):
    """CRUD for documents plus sharing and file-import actions.

    A user sees documents they own and documents shared with them. Object-level
    permissions gate read/write/delete; sharing endpoints are owner-only.
    """

    permission_classes = [IsAuthenticated, DocumentAccessPermission]

    def get_serializer_class(self):
        if self.action == "list":
            return DocumentListSerializer
        return DocumentDetailSerializer

    def get_queryset(self):
        user = self.request.user
        # Owned OR shared-with-me, de-duplicated, with shares/owner prefetched.
        return (
            Document.objects.filter(Q(owner=user) | Q(shares__user=user))
            .distinct()
            .select_related("owner")
            .prefetch_related("shares__user")
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # --- Sharing ----------------------------------------------------------
    def _require_owner(self, document):
        return document.owner_id == self.request.user.id

    @action(detail=True, methods=["get", "post"])
    def shares(self, request, pk=None):
        """GET: list shares. POST: grant access by email with a role."""
        document = self.get_object()  # runs object permission check (view)
        if request.method == "GET":
            serializer = ShareSerializer(document.shares.all(), many=True)
            return Response(serializer.data)

        # POST -> owner only
        if not self._require_owner(document):
            return Response(
                {"detail": "Only the owner can share this document."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ShareCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]

        try:
            target = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"email": [f"No user found with email '{email}'."]},
                status=status.HTTP_404_NOT_FOUND,
            )

        if target.id == document.owner_id:
            return Response(
                {"email": ["You already own this document."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        share, created = Share.objects.update_or_create(
            document=document,
            user=target,
            defaults={"role": role, "created_by": request.user},
        )
        out = ShareSerializer(share)
        return Response(
            out.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path="shares/(?P<share_id>[^/.]+)",
    )
    def remove_share(self, request, pk=None, share_id=None):
        """Revoke a single share. Owner only."""
        document = self.get_object()
        if not self._require_owner(document):
            return Response(
                {"detail": "Only the owner can manage sharing."},
                status=status.HTTP_403_FORBIDDEN,
            )
        deleted, _ = Share.objects.filter(
            document=document, id=share_id
        ).delete()
        if not deleted:
            return Response(
                {"detail": "Share not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    # --- File import ------------------------------------------------------
    @action(detail=False, methods=["post"], url_path="import")
    def import_document(self, request):
        """Create a new document from an uploaded .txt / .md file."""
        upload = request.FILES.get("file")
        if upload is None:
            return Response(
                {"file": ["No file was uploaded under the 'file' field."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_bytes = settings.MAX_IMPORT_FILE_BYTES
        if upload.size > max_bytes:
            return Response(
                {"file": [f"File too large (max {max_bytes // 1024} KB)."]},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        try:
            title, html_content = import_file(upload.name, upload.read())
        except ImportError_ as exc:
            return Response(
                {"file": [str(exc)], "supported": sorted(SUPPORTED_EXTENSIONS)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document = Document.objects.create(
            owner=request.user, title=title, content=html_content
        )
        serializer = DocumentDetailSerializer(
            document, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """Authenticate by email + password and return an auth token.

    Seeded users log in with their email. We resolve the email to a username
    (Django's default auth backend authenticates by username) and return a
    stable token the SPA stores and sends as ``Authorization: Token <key>``.
    """
    email = (request.data.get("email") or "").strip().lower()
    password = request.data.get("password") or ""
    if not email or not password:
        return Response(
            {"detail": "Both 'email' and 'password' are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user_obj = User.objects.filter(email__iexact=email).first()
    user = (
        authenticate(username=user_obj.username, password=password)
        if user_obj
        else None
    )
    if user is None:
        return Response(
            {"detail": "Invalid email or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": UserSerializer(user).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the currently authenticated user."""
    return Response(UserSerializer(request.user).data)

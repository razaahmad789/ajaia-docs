"""Automated tests for the core product logic.

Focus: the access-control rules that make sharing correct and safe, plus the
file-import path and content sanitization. These are the parts where a bug
would be a real product/security problem, so they get the coverage.
"""
import io

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .importers import import_file
from .models import Document, Share
from .sanitize import sanitize_html

User = get_user_model()


def make_user(username, password="pw-123456"):
    return User.objects.create_user(
        username=username, email=f"{username}@example.com", password=password
    )


class AuthTests(APITestCase):
    def setUp(self):
        self.user = make_user("alice")

    def test_login_with_email_returns_token(self):
        resp = self.client.post(
            reverse("auth-login"),
            {"email": "alice@example.com", "password": "pw-123456"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("token", resp.data)
        self.assertEqual(resp.data["user"]["email"], "alice@example.com")

    def test_login_rejects_bad_password(self):
        resp = self.client.post(
            reverse("auth-login"),
            {"email": "alice@example.com", "password": "wrong"},
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_documents_require_authentication(self):
        resp = self.client.get(reverse("document-list"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class DocumentSharingTests(APITestCase):
    """The heart of the sharing model: who can see/edit/delete what."""

    def setUp(self):
        self.alice = make_user("alice")
        self.bob = make_user("bob")
        self.carol = make_user("carol")
        self.doc = Document.objects.create(
            owner=self.alice, title="Alice's doc", content="<p>hello</p>"
        )

    def test_list_shows_owned_and_shared_but_not_others(self):
        # Share with Bob as viewer.
        Share.objects.create(
            document=self.doc, user=self.bob, role=Share.Role.VIEWER
        )
        # Bob sees the shared doc; Carol sees nothing.
        self.client.force_authenticate(self.bob)
        resp = self.client.get(reverse("document-list"))
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["role"], "viewer")
        self.assertFalse(resp.data[0]["is_owner"])

        self.client.force_authenticate(self.carol)
        resp = self.client.get(reverse("document-list"))
        self.assertEqual(len(resp.data), 0)

    def test_non_shared_user_cannot_read_document(self):
        self.client.force_authenticate(self.carol)
        resp = self.client.get(
            reverse("document-detail", args=[self.doc.id])
        )
        # Not in queryset -> 404 (don't leak existence).
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewer_cannot_edit(self):
        Share.objects.create(
            document=self.doc, user=self.bob, role=Share.Role.VIEWER
        )
        self.client.force_authenticate(self.bob)
        resp = self.client.patch(
            reverse("document-detail", args=[self.doc.id]),
            {"content": "<p>hacked</p>"},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.content, "<p>hello</p>")

    def test_editor_can_edit(self):
        Share.objects.create(
            document=self.doc, user=self.bob, role=Share.Role.EDITOR
        )
        self.client.force_authenticate(self.bob)
        resp = self.client.patch(
            reverse("document-detail", args=[self.doc.id]),
            {"content": "<p>updated by bob</p>"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.content, "<p>updated by bob</p>")

    def test_only_owner_can_delete(self):
        Share.objects.create(
            document=self.doc, user=self.bob, role=Share.Role.EDITOR
        )
        self.client.force_authenticate(self.bob)
        resp = self.client.delete(
            reverse("document-detail", args=[self.doc.id])
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.alice)
        resp = self.client.delete(
            reverse("document-detail", args=[self.doc.id])
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Document.objects.filter(id=self.doc.id).exists())

    def test_owner_can_share_by_email(self):
        self.client.force_authenticate(self.alice)
        resp = self.client.post(
            reverse("document-shares", args=[self.doc.id]),
            {"email": "bob@example.com", "role": "editor"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["role"], "editor")
        self.assertTrue(
            Share.objects.filter(document=self.doc, user=self.bob).exists()
        )

    def test_share_with_unknown_email_returns_404(self):
        self.client.force_authenticate(self.alice)
        resp = self.client.post(
            reverse("document-shares", args=[self.doc.id]),
            {"email": "nobody@example.com", "role": "viewer"},
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_owner_cannot_share(self):
        Share.objects.create(
            document=self.doc, user=self.bob, role=Share.Role.EDITOR
        )
        self.client.force_authenticate(self.bob)
        resp = self.client.post(
            reverse("document-shares", args=[self.doc.id]),
            {"email": "carol@example.com", "role": "viewer"},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_resharing_updates_role(self):
        self.client.force_authenticate(self.alice)
        url = reverse("document-shares", args=[self.doc.id])
        self.client.post(url, {"email": "bob@example.com", "role": "viewer"})
        resp = self.client.post(
            url, {"email": "bob@example.com", "role": "editor"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Share.objects.get(user=self.bob).role, "editor")

    def test_owner_can_revoke_share(self):
        share = Share.objects.create(
            document=self.doc, user=self.bob, role=Share.Role.VIEWER
        )
        self.client.force_authenticate(self.alice)
        resp = self.client.delete(
            reverse("document-remove-share", args=[self.doc.id, share.id])
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Share.objects.filter(id=share.id).exists())


class ContentSanitizationTests(APITestCase):
    def test_sanitize_strips_script_tags(self):
        dirty = "<p>ok</p><script>alert('xss')</script>"
        clean = sanitize_html(dirty)
        self.assertNotIn("<script>", clean)
        self.assertIn("<p>ok</p>", clean)

    def test_sanitize_strips_event_handlers(self):
        dirty = '<p onclick="evil()">text</p><img src=x onerror=alert(1)>'
        clean = sanitize_html(dirty)
        self.assertNotIn("onclick", clean)
        self.assertNotIn("onerror", clean)
        self.assertNotIn("<img", clean)

    def test_content_sanitized_on_create(self):
        alice = make_user("alice")
        self.client.force_authenticate(alice)
        resp = self.client.post(
            reverse("document-list"),
            {
                "title": "Doc",
                "content": "<p>hi</p><script>alert(1)</script>",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("script", resp.data["content"])

    def test_blank_title_rejected(self):
        alice = make_user("alice")
        self.client.force_authenticate(alice)
        resp = self.client.post(
            reverse("document-list"), {"title": "   ", "content": ""}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class ImportTests(APITestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.client.force_authenticate(self.alice)

    def test_import_markdown_creates_document(self):
        md = b"# Title\n\nSome **bold** text.\n\n- a\n- b\n"
        upload = io.BytesIO(md)
        upload.name = "notes.md"
        resp = self.client.post(
            reverse("document-import-document"),
            {"file": upload},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["title"], "notes")
        self.assertIn("<h1>", resp.data["content"])
        self.assertIn("<strong>bold</strong>", resp.data["content"])
        self.assertIn("<li>", resp.data["content"])

    def test_import_plaintext_creates_paragraphs(self):
        txt = b"First paragraph.\n\nSecond paragraph."
        upload = io.BytesIO(txt)
        upload.name = "note.txt"
        resp = self.client.post(
            reverse("document-import-document"),
            {"file": upload},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["content"].count("<p>"), 2)

    def test_import_rejects_unsupported_type(self):
        upload = io.BytesIO(b"\x00\x01binary")
        upload.name = "image.png"
        resp = self.client.post(
            reverse("document-import-document"),
            {"file": upload},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_import_unit_sanitizes_dangerous_markdown(self):
        # Markdown allows raw HTML; ensure the import path sanitizes it.
        title, html = import_file(
            "x.md", b"# Hi\n\n<script>alert(1)</script>\n"
        )
        self.assertEqual(title, "x")
        self.assertNotIn("<script>", html)
        self.assertIn("<h1>", html)

from rest_framework import permissions


class DocumentAccessPermission(permissions.BasePermission):
    """Object-level access control for documents.

    - Any authenticated user with a view/edit role (owner or share) may read.
    - Writing (PUT/PATCH) requires an editor or owner role.
    - Destroying and managing shares is owner-only (enforced in the view).
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return obj.can_view(user)
        if request.method == "DELETE":
            return obj.owner_id == user.id
        # PUT / PATCH
        return obj.can_edit(user)

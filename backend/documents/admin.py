from django.contrib import admin

from .models import Document, Share


class ShareInline(admin.TabularInline):
    model = Share
    extra = 0
    autocomplete_fields = ["user"]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "updated_at", "created_at"]
    search_fields = ["title", "owner__username", "owner__email"]
    list_filter = ["created_at", "updated_at"]
    inlines = [ShareInline]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ["document", "user", "role", "created_by", "created_at"]
    list_filter = ["role"]
    search_fields = ["document__title", "user__username", "user__email"]

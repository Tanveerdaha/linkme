"""Admin registration for profiles."""

from django.contrib import admin

from apps.profiles.models import Profile, ProfileSection


class ProfileSectionInline(admin.TabularInline):
    model = ProfileSection
    extra = 0


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "headline",
        "location",
        "profile_visibility",
        "updated_at",
    )
    list_filter = ("profile_visibility",)
    search_fields = (
        "user__username",
        "user__email",
        "headline",
        "bio",
        "location",
    )
    raw_id_fields = ("user",)
    inlines = [ProfileSectionInline]


@admin.register(ProfileSection)
class ProfileSectionAdmin(admin.ModelAdmin):
    list_display = ("profile", "section_type", "order", "visibility")
    list_filter = ("section_type", "visibility")
    raw_id_fields = ("profile",)

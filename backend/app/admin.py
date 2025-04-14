# File: Bivaset-Service-app/backend/app/admin.py

from django.contrib import admin
from django.contrib.gis import admin as gis_admin # Use GIS admin for models with PointField
from .models import User, Project, Proposal, Category, ProjectFile

# Inline Admin for Project Files within Project Admin
class ProjectFileInline(admin.TabularInline):
    model = ProjectFile
    extra = 1 # Number of extra empty forms to display
    # readonly_fields = ('file_preview',) # Optional: Add a preview if you implement it in the model

    # Optional: Preview for images (requires changes in models.py to add this method)
    # def file_preview(self, obj):
    #     if obj.file and hasattr(obj.file, 'url'):
    #         # Add basic check for image types
    #         image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    #         if any(obj.file.url.lower().endswith(ext) for ext in image_extensions):
    #             from django.utils.html import format_html
    #             return format_html('<img src="{}" width="150" height="auto" />', obj.file.url)
    #     return "(No preview)"
    # file_preview.short_description = 'Preview'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent', 'get_children_count')
    list_filter = ('parent',)
    search_fields = ('name',)
    ordering = ('parent__name', 'name') # Order by parent then by name

    def get_children_count(self, obj):
        return obj.children.count()
    get_children_count.short_description = 'Subcategories Count'

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone', 'name', 'role', 'telegram_id', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('phone', 'name', 'telegram_id')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {'fields': ('phone', 'name', 'role')}),
        ('Telegram Info', {'fields': ('telegram_id', 'telegram_phone'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    ordering = ('-created_at',)

@admin.register(Project)
class ProjectAdmin(gis_admin.OSMGeoAdmin): # Use OSMGeoAdmin for PointField visualization
    list_display = ('id', 'title', 'user_display', 'category', 'status', 'service_location', 'created_at', 'deadline_date')
    list_filter = ('status', 'service_location', 'category', 'created_at', 'deadline_date')
    search_fields = ('id', 'title', 'description', 'user__phone', 'user__name', 'category__name')
    readonly_fields = ('id', 'created_at', 'user_display')
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    inlines = [ProjectFileInline] # Show project files inline

    fieldsets = (
        (None, {'fields': ('id', 'title', 'user_display', 'category', 'status')}),
        ('Details', {'fields': ('description', 'budget')}),
        ('Location', {'fields': ('service_location', 'location', 'address')}), # Use OSMGeoAdmin map widget
        ('Dates', {'fields': ('start_date', 'deadline_date', 'expiry_date'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

    def user_display(self, obj):
        return f"{obj.user.name} ({obj.user.phone})"
    user_display.short_description = 'User'

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_link', 'contractor_link', 'price', 'time', 'submitted_at')
    list_filter = ('submitted_at', 'project__category')
    search_fields = ('project__title', 'contractor__phone', 'contractor__name')
    readonly_fields = ('submitted_at', 'project_link', 'contractor_link')
    list_per_page = 25
    ordering = ('-submitted_at',)

    fieldsets = (
        (None, {'fields': ('project_link', 'contractor_link')}),
        ('Proposal Details', {'fields': ('price', 'time')}),
        ('Timestamps', {'fields': ('submitted_at',), 'classes': ('collapse',)}),
    )

    # Add links to related project and contractor
    def project_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse("admin:app_project_change", args=[obj.project.id])
        return format_html('<a href="{}">{} (ID: {})</a>', link, obj.project.title, obj.project.id)
    project_link.short_description = 'Project'

    def contractor_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse("admin:app_user_change", args=[obj.contractor.id])
        return format_html('<a href="{}">{} ({})</a>', link, obj.contractor.name, obj.contractor.phone)
    contractor_link.short_description = 'Contractor'

# Note: ProjectFile is managed via ProjectAdmin Inline, no need to register separately unless desired.
# If you want a separate view for ProjectFile:
# @admin.register(ProjectFile)
# class ProjectFileAdmin(admin.ModelAdmin):
#     list_display = ('id', 'project', 'file')
#     search_fields = ('project__title', 'file')
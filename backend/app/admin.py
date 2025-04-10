from django.contrib import admin
from .models import User, Project, Proposal, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent', 'get_children')
    list_filter = ('parent',)
    search_fields = ('name',)
    
    def get_children(self, obj):
        return ", ".join([child.name for child in obj.children.all()])
    get_children.short_description = 'Children'

admin.site.register(User)
admin.site.register(Project)
admin.site.register(Proposal)

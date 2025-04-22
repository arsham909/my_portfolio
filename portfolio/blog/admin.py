from django.contrib import admin
from .models import Post

# Register your models here.
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'author', 'publish']
    list_filter = ['title', 'created', 'publish', 'author']
    search_fields = ['title', 'body']
    prepopulated_fields = {'slug':('title',)}
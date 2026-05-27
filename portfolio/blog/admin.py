from django.contrib import admin
from django.utils.html import format_html_join, format_html

from .models import Post, PostImage, Comment


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 3
    fields = ['image', 'caption', 'alt_text', 'order']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'author', 'publish', 'status']
    list_filter = ['status', 'created', 'publish', 'author']
    search_fields = ['title', 'body']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    date_hierarchy = 'publish'
    ordering = ['status', 'publish']
    show_facets = admin.ShowFacets.ALWAYS
    inlines = [PostImageInline]
    readonly_fields = ['image_shortcodes']

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'status', 'publish', 'tags', 'image'),
        }),
        ('Body', {
            'fields': ('body', 'image_shortcodes'),
            'description': (
                'To place an image between paragraphs, paste its shortcode '
                '(e.g. <code>{% post_image 3 %}</code>) on its own line in the '
                'body markdown where you want it to appear. Upload images first, '
                'save, then copy the shortcode from the table below.'
            ),
        }),
    )

    def image_shortcodes(self, obj):
        if not obj or not obj.pk:
            return '(save the post first to upload images and see shortcodes)'
        images = obj.images.all()
        if not images:
            return '(no inline images yet — add some in the Images section)'
        rows = format_html_join(
            '',
            '<tr><td><code style="cursor:text;user-select:all">{{% post_image {} %}}</code></td>'
            '<td><a href="{}" target="_blank">{}</a></td><td>{}</td></tr>',
            ((img.pk, img.image.url, img.image.url, img.caption or '—') for img in images),
        )
        return format_html(
            '<table style="border-collapse:collapse"><thead><tr>'
            '<th style="text-align:left;padding:4px 8px">shortcode</th>'
            '<th style="text-align:left;padding:4px 8px">url</th>'
            '<th style="text-align:left;padding:4px 8px">caption</th>'
            '</tr></thead><tbody>{}</tbody></table>',
            rows,
        )
    image_shortcodes.short_description = 'Inline image shortcodes'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'post', 'created', 'active']
    list_filter = ['active', 'name', 'created', 'updated']
    search_fields = ['name', 'email', 'body']
    actions = ('approve_comments',)

    @admin.action(description='Approve selected comments')
    def approve_comments(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} comment(s) approved.')

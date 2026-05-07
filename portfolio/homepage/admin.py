from django.contrib import admin
from django.utils.html import format_html, format_html_join

from .models import Project, ProjectImage


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ('image', 'caption', 'alt_text', 'order', 'preview')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="max-height:80px;border-radius:4px;">', obj.image.url)
        return ''
    preview.short_description = 'preview'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_featured', 'is_published', 'demo_url', 'github_url', 'updated')
    list_editable = ('order', 'is_featured', 'is_published')
    list_filter = ('is_featured', 'is_published')
    search_fields = ('title', 'summary', 'body', 'tech')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProjectImageInline]
    readonly_fields = ('cover_preview', 'image_shortcodes', 'created', 'updated')
    fieldsets = (
        ('Card (home page)', {
            'fields': ('title', 'slug', 'summary', 'tech', 'cover_image', 'cover_preview', 'is_featured', 'order'),
        }),
        ('Detail page', {
            'fields': ('body', 'image_shortcodes', 'youtube_url', 'demo_url', 'github_url'),
            'description': 'Body uses Markdown. Save first, then paste a shortcode below into the body where you want each gallery image to appear inline.',
        }),
        ('Meta', {
            'fields': ('is_published', 'created', 'updated'),
            'classes': ('collapse',),
        }),
    )

    def cover_preview(self, obj):
        if obj and obj.cover_image:
            return format_html('<img src="{}" style="max-height:160px;border-radius:6px;">', obj.cover_image.url)
        return ''
    cover_preview.short_description = 'cover preview'

    def image_shortcodes(self, obj):
        if not obj or not obj.pk:
            return '(save the project first to upload gallery images and see shortcodes)'
        images = obj.images.all()
        if not images:
            return '(no gallery images yet — add some in the Images section below)'
        rows = format_html_join(
            '',
            '<tr><td style="padding:4px 8px"><code>{{% project_image {} %}}</code></td>'
            '<td style="padding:4px 8px"><a href="{}" target="_blank">view</a></td>'
            '<td style="padding:4px 8px">{}</td></tr>',
            ((img.pk, img.image.url, img.caption or '—') for img in images),
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

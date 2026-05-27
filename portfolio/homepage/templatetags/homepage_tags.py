import math
import re

import markdown
from django import template
from django.template.defaultfilters import truncatewords_html
from django.utils.html import escape, strip_tags
from django.utils.safestring import mark_safe

from common.sanitize import clean_html
from ..models import ProjectImage

register = template.Library()

# Shortcodes are expanded *after* markdown rendering so authors can drop
# {% project_image N %} between paragraphs and get a <figure> inline.
PROJECT_SHORTCODE_RE = re.compile(r'\{%\s*project_image\s+(\d+)\s*%\}')
MARKDOWN_IMAGE_RE = re.compile(r'!\[[^\]]*\]\([^)]*\)')


def _render_project_shortcode(match):
    pk = int(match.group(1))
    try:
        img = ProjectImage.objects.get(pk=pk)
    except ProjectImage.DoesNotExist:
        return ''
    alt = escape(img.alt_text or img.caption or '')
    caption_html = f'<figcaption>{escape(img.caption)}</figcaption>' if img.caption else ''
    return (
        f'<figure class="post-figure">'
        f'<img src="{img.image.url}" alt="{alt}" loading="lazy">'
        f'{caption_html}'
        f'</figure>'
    )


@register.filter(name='project_markdown')
def project_markdown(text):
    rendered = markdown.markdown(text or '', extensions=['extra'], output_format='html')
    rendered = PROJECT_SHORTCODE_RE.sub(_render_project_shortcode, rendered)
    rendered = clean_html(rendered)
    return mark_safe(rendered)


@register.filter(name='reading_time')
def reading_time(text):
    if not text:
        return 1
    words = len(strip_tags(text).split())
    return max(1, math.ceil(words / 200))

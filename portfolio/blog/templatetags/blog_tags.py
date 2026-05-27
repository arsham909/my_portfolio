import re

import markdown
from django import template
from django.db.models import Count
from django.template.defaultfilters import truncatewords_html
from django.utils.html import escape, strip_tags
from django.utils.safestring import mark_safe

from common.sanitize import clean_html
from ..models import Post, PostImage

register = template.Library()

MARKDOWN_IMAGE_RE = re.compile(r'!\[[^\]]*\]\([^)]*\)')


@register.simple_tag
def total_posts():
    return Post.published.count()


@register.inclusion_tag('blog/post/latest_posts.html')
def show_latest_posts(count=5):
    return {'latest_posts': Post.published.order_by('-publish')[:count]}


@register.simple_tag
def get_most_commented_posts(count=5):
    return (
        Post.published
        .annotate(total_comments=Count('comments'))
        .order_by('-total_comments')[:count]
    )


# Shortcodes are expanded *after* markdown rendering so authors can drop
# {% post_image N %} between paragraphs and get a <figure> inline.
SHORTCODE_RE = re.compile(r'\{%\s*post_image\s+(\d+)\s*%\}')


def _render_shortcode(match):
    pk = int(match.group(1))
    try:
        img = PostImage.objects.get(pk=pk)
    except PostImage.DoesNotExist:
        return ''
    alt = escape(img.alt_text or img.caption or '')
    caption_html = f'<figcaption>{escape(img.caption)}</figcaption>' if img.caption else ''
    return (
        f'<figure class="post-figure">'
        f'<img src="{img.image.url}" alt="{alt}" loading="lazy">'
        f'{caption_html}'
        f'</figure>'
    )


@register.filter(name='markdown')
def markdown_format(text):
    """Render author-controlled markdown, then expand {% post_image N %} shortcodes.

    Only safe to apply to author content (Post.body), never to user-submitted text.
    """
    rendered = markdown.markdown(text or '', extensions=['extra'], output_format='html')
    rendered = SHORTCODE_RE.sub(_render_shortcode, rendered)
    rendered = clean_html(rendered)
    return mark_safe(rendered)


@register.filter(name='card_excerpt')
def card_excerpt(text, words=20):
    """Plain-text excerpt: strip shortcodes/markdown images, render markdown, truncate."""
    cleaned = SHORTCODE_RE.sub('', text or '')
    cleaned = MARKDOWN_IMAGE_RE.sub('', cleaned)
    rendered = markdown.markdown(cleaned, extensions=['extra'], output_format='html')
    plain = strip_tags(rendered).strip()
    return truncatewords_html(plain, words)


def extract_used_image_pks(body):
    """Return the set of PostImage pks referenced via shortcodes in `body`."""
    return {int(m.group(1)) for m in SHORTCODE_RE.finditer(body or '')}

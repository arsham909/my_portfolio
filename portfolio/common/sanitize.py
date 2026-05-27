import bleach


ALLOWED_TAGS = [
    'p', 'br', 'hr',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'strong', 'em', 'u', 's',
    'ul', 'ol', 'li',
    'blockquote', 'pre', 'code',
    'a', 'img', 'figure', 'figcaption',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'span', 'div',
]

ALLOWED_ATTRS = {
    'a': ['href', 'title', 'rel', 'target'],
    'img': ['src', 'alt', 'title', 'loading', 'width', 'height'],
    'figure': ['class'],
    'span': ['class'],
    'div': ['class'],
    'code': ['class'],
    'pre': ['class'],
    'th': ['scope'],
}


def clean_html(html: str) -> str:
    """Whitelist-sanitize markdown-rendered HTML.

    Why: authors are trusted, but a compromised-admin scenario or a
    simple paste of raw HTML with onclick= should not become XSS.
    """
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        strip=True,
    )

import markdown
from django.contrib.syndication.views import Feed
from django.template.defaultfilters import truncatewords_html
from django.urls import reverse_lazy
from .models import Post
from .templatetags.blog_tags import SHORTCODE_RE, MARKDOWN_IMAGE_RE

class LatestPostsFeed(Feed):
    
    title = 'My blog'
    link = reverse_lazy('blog:post_list')
    description = 'New posts of my blog.'
    
    def items(self):
        return Post.published.all()[:5]
    
    def item_title(self, item):
        return item.title
    
    def item_description(self, item):
        cleaned = SHORTCODE_RE.sub('', item.body or '')
        cleaned = MARKDOWN_IMAGE_RE.sub('', cleaned)
        return truncatewords_html(markdown.markdown(cleaned), 30)
    
    def item_pubdate(self, item):
        return item.publish
    
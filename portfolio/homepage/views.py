from django.shortcuts import render
from blog.models import Post
from blog.views import PostListView

# Create your views here.
def homepage(request):
    recentPosts = Post.published.order_by('-publish')[:3]
    projects = Post.published.filter(tags__in=[8])
    
    return render(request, "homepage/homepage.html",{'recentPosts':recentPosts, 'projects':projects} )
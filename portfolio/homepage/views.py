from django.shortcuts import render
from blog.models import Post
from blog.views import PostListView

# Create your views here.
def homepage(request):
    recentPosts = Post.published.order_by('-publish')[:3]
    
    return render(request, "homepage/homepage.html",{'recentPosts':recentPosts})
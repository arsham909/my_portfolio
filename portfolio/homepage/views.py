from django.shortcuts import render
from blog.models import Post
from blog.views import PostListView
from .form import ContactMe , contact_me_form
from django.core.mail import send_mail

# Create your views here.
def homepage(request):
    sent = False
    if request.method =='POST':
        form = ContactMe(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            sender = contact_me_form(cd)
            send_mail(
                subject=sender['subject'],
                message=sender['message'],
                from_email=None,
                recipient_list=['arsham202@gmail.com']
            )
            sent = True
    else:
        form = ContactMe()
        recentPosts = Post.published.order_by('-publish')[:3]
        projects = Post.published.filter(tags__in=[8])
    
    return render(request, "homepage/homepage.html",{'recentPosts':recentPosts, 'projects':projects, 'form':form , 'sent':sent} )

def contact_me(request):
    sent = False
    if request.method =='POST':
        form = ContactMe(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            sender = contact_me_form(cd)
            send_mail(
                subject=sender['subject'],
                message=sender['message'],
                from_email=None,
                recipient_list=['arsham202@gmail.com']
            )
            sent = True
    else:
        form = ContactMe()
    return render(request, 'homepage/contactme.html',{'form':form, 'sent':sent})

def about_me(request):
    if request.method == "GET":
        return render(request, 'homepage/aboutme.html', )
import os

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.mail import send_mail

from blog.models import Post
from .forms import ContactMe, contact_me_form
from .models import Project


CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL', 'arsham202@gmail.com')


def _handle_contact(request):
    sent = False
    if request.method == 'POST':
        form = ContactMe(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            sender = contact_me_form(cd)
            send_mail(
                subject=sender['subject'],
                message=sender['message'],
                from_email=None,
                recipient_list=[CONTACT_EMAIL],
            )
            sent = True
    else:
        form = ContactMe()
    return form, sent


def homepage(request):
    form, sent = _handle_contact(request)
    recentPosts = Post.published.order_by('-publish')[:3]
    featured_projects = Project.published.filter(is_featured=True)[:6]
    return render(
        request,
        "homepage/homepage.html",
        {
            'recentPosts': recentPosts,
            'featured_projects': featured_projects,
            'form': form,
            'sent': sent,
        },
    )


def contact_me(request):
    form, sent = _handle_contact(request)
    return render(request, 'homepage/contactme.html', {'form': form, 'sent': sent})


def about_me(request):
    projects = Project.published.all()
    return render(request, 'homepage/aboutme.html', {'projects': projects})


def project_list(request):
    projects = Project.published.all()
    return render(request, 'homepage/project_list.html', {'projects': projects})


def project_detail(request, slug):
    project = get_object_or_404(Project.published, slug=slug)
    return render(request, 'homepage/project_detail.html', {'project': project})


def healthz(request):
    return JsonResponse({'status': 'ok'})


def handler404(request, exception):
    return render(request, '404.html', status=404)

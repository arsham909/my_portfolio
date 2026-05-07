from django.urls import path
from . import views

app_name = 'homepage'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('home', views.homepage, name='home'),
    path('contactme', views.contact_me, name='contactme'),
    path('aboutme', views.about_me, name='aboutme'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/<slug:slug>/', views.project_detail, name='project_detail'),
    path('healthz/', views.healthz, name='healthz'),
]

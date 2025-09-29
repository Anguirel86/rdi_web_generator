from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'generator'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
]

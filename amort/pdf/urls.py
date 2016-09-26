from django.conf.urls import url
from django.contrib import admin

from . import views

urlpatterns = [
    url('^pdf$', views.AmortPdfView.as_view(), name='amort_pdf'),
]

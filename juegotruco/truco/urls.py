from django.conf.urls import patterns, url

from truco import views

urlpatterns = patterns('',
    url(r'^lobby$', views.lobby, name='lobby'),
)

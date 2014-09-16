from django.conf.urls import patterns, url

from truco import views

urlpatterns = patterns('',
    url(r'^login$', views.my_login, name='login'),
    url(r'^index$', views.index, name='index'),
    url(r'^create_user$', views.my_create_user, name='create_user'),
    url(r'^logout$', views.my_logout, name='logout'),
)

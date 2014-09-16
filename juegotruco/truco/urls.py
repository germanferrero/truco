from django.conf.urls import patterns, url

from truco import views

urlpatterns = patterns('',
    url(r'^login$', views.my_login, name='login'),
    url(r'^index$', views.index, name='index'),
)

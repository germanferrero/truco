from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^truco/', include('truco.urls', namespace="truco")),
    url(r'^usuarios/', include('usuarios.urls', namespace="usuarios")),
)

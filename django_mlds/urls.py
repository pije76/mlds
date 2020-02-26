"""django_mlds URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static

from acefs.views import *


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main, name='main'),
    path('output/', output, name='output'),
    path('secret-back-door/', backdoor, name='backdoor'),
    path('visitors/', visitors, name='visitors'),
    re_path('visitor_list/(?P<page_num>[0-9]*)', visitor_list, name='visitor_list'),
    re_path('visitor_detail/(?P<visitor_id>[0-9]*)', visitor_detail, name='visitor_detail'),

]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    import debug_toolbar
#    urlpatterns = [
#        path('__debug__/', include(debug_toolbar.urls)),

    # For django versions before 2.0:
    # url(r'^__debug__/', include(debug_toolbar.urls)),

#    ] + urlpatterns
    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]

from django.conf.urls.defaults import patterns, include, url
from .views import *
from django.contrib.auth.decorators import login_required

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # admin
    #url(r'^admin/', include(admin.site.urls)),

    # staff apps
    url(r'^file_upload/', login_required(file_upload_view), name='file_upload'),
    url(r'^file_review/', login_required(file_review_view), name='file_review'),
    url(r'^data_digest/', login_required(data_digest_view), name='data_digest'),
    url(r'^mts_load/', login_required(mts_load_view), name='mts_load'),
    url(r'^archive/', login_required(archive_view), name='archive'),
    url(r'^help/', login_required(help_view), name='help'),
    url(r'^', login_required(file_upload_view), name='default'),
)


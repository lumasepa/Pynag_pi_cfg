from django.conf.urls import patterns, include, url
from main.views import Index


urlpatterns = patterns('',

                    url(r'/index.html', Index.as_view()),
                    url(r'$', Index.as_view()),
)
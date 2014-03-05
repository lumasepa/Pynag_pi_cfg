from django.conf.urls import patterns, include, url
from main.views import Index, NagiosCfg


urlpatterns = patterns('',

                    url(r'index.html', Index.as_view()),
                    url(r'nagios.cfg', NagiosCfg.as_view(), name='nagios-cfg'),
                    url(r'$', Index.as_view()),

)
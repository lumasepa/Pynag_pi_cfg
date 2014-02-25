from django.conf.urls import patterns, include, url
from main.views import Index, NagiosCfg, Confssh


urlpatterns = patterns('',

                    url(r'index.html', Index.as_view()),
                    url(r'nagios.cfg', NagiosCfg.as_view(), name='nagios-cfg'),
                    url(r'confssh.html', Confssh.as_view(), name='confssh'),
                    url(r'$', Index.as_view()),

)
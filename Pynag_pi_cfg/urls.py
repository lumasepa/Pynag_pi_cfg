from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'Pynag_pi_cfg.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^services.yml', 'main.views.services_list', name='services'),

    url(r'^hosts.yml', 'main.views.hosts_list', name='hosts'),

    url(r'^sondas.yml', 'main.views.sondas_list', name='sondas'),

    url(r'^hostsservicessondas.yml', 'main.views.hostsservicessondas_list', name='hostsservicessondas'),

)

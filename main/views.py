from main.models import Services, Hosts, Sondas, HostsServicesSondas
from django.views.generic import TemplateView
from fabric.api import env, run, put
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
import sys

nagConfHost = \
    """
define host{
    use             generic-host
    host_name       $1
    alias           $2
    address         $1
    }
    """
nagConfService = \
    """
define service{
    use                     passive-service
    host_name               $1
    service_description     $2
    freshness_threshold     $3
    contact_groups          $4
    }
    """

scriptSnippet = \
    """
MESSAGE=`$DIR_PLUGINGS/$2`
STATUS=$?
ssend_nsca "$HOST" "$SERVICE" "$STATUS" "$MESSAGE"
"""

scriptInit = \
"""#!/bin/bash

NSCA_CONF_FILE="/etc/send_nsca.cfg"

DIR_PLUGINGS="/usr/lib/nagios/plugins"

NAGIOS_SERVER="193.145.118.253"

function ssend_nsca
{
	echo -e "$1\t$2\t$3\t$4" | /usr/sbin/send_nsca -H $NAGIOS_SERVER -c $NSCA_CONF_FILE
}

    """


class Index(TemplateView):

    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        if request.GET.get('sendcfg', '') == "1" or request.POST.get('sendcfg', '') == "1":
            print ("Creando configuraciones")
            try:
                nagiosCfg = open('nagios-dist.cfg', 'w')

                sondas = Sondas.objects.all()
                services = Services.objects.all()
                hosts = Hosts.objects.all()
                hostsservicessondas = HostsServicesSondas.objects.all()

                for host in hosts:
                    cfgHost = nagConfHost.replace("$1", host.address)
                    cfgHost = cfgHost.replace("$2", host.name)
                    nagiosCfg.write(cfgHost)

                for sonda in sondas:
                    script = open("checks-" + sonda.name + ".sh", 'w')
                    script.write(scriptInit)

                for hostservicesonda in hostsservicessondas:

                    cfgService = nagConfService.replace("$1", hostservicesonda.host.name)
                    cfgService = cfgService.replace("$2", hostservicesonda.service.name + "_" + hostservicesonda.sonda.name)
                    cfgService = cfgService.replace("$3", str(hostservicesonda.freshness_threshold))
                    cfgService = cfgService.replace("$4", hostservicesonda.contact)
                    nagiosCfg.write(cfgService)

                    script = open("checks-" + hostservicesonda.sonda.name + ".sh", 'a')
                    if hostservicesonda.service.pluging:
                        snipet = scriptSnippet.replace("$2", hostservicesonda.service.command)
                        snipet = snipet.replace("$HOST", hostservicesonda.host.address)
                        snipet = snipet.replace("$SERVICE", hostservicesonda.service.name + "_" + hostservicesonda.sonda.name)
                        script.write(snipet)
                    else:
                        script.write(hostservicesonda.service.command.replace("$HOST", hostservicesonda.host.address))
                    script.close()


                crontab = 'echo "10,20,30,40,50,00 * * * * root /root/$1" >> /etc/crontab'

                for sonda in sondas:
                    print(sonda.address)
                    env.host_string = str(sonda.address)
                    env.user = sonda.user
                    env.password = sonda.passwd
                    put("checks-" + sonda.name + ".sh", "/root/" + "checks-" + sonda.name + ".sh")
                    run(crontab.replace("$1", "checks-" + sonda.name + ".sh"))
                    run("chmod +x /root/" + "checks-" + sonda.name + ".sh")
            except:
                c = {}
                c.update(csrf(request))
                c['body'] = "Unexpected error:" #+ sys.exc_info()[0]
                response = render_to_response('index.html', c)
                return response
                raise
            c = {}
            c.update(csrf(request))
            c['body'] = "<h1>Configuraciones enviadas correctamente<\h1>"
            response = render_to_response('index.html', c)
            return response

        else:
            print ("get o post sin parametros usados")
            for x in request.POST:
                print(x)
            c = {}
            c.update(csrf(request))
            c['HostsServicesSondas'] = HostsServicesSondas.objects.all()
            response = render_to_response('index.html', c)
            return response

    def post(self, request, *args, **kwargs):
        return self.get(request, args, kwargs)




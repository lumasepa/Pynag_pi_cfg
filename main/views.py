from main.models import Service, Host, Sonda, HostsServicesSondas
from django.views.generic import TemplateView
from fabric.api import env, run, put
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
import sys
from rest_framework.views import Response, APIView
from rest_framework import status as httpstatus
from django.template import Template, Context



scriptSnippet = \
    """
MESSAGE=`$DIR_PLUGINGS/$2`
ssend_nsca "$HOST" "$SERVICE" "$?" "$MESSAGE"
"""


class Index(TemplateView):

    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        if request.GET.get('sendcfg', '') == "1" or request.POST.get('sendcfg', '') == "1":
            print ("Creando configuraciones")
            try:
                scripts = {}
                sondas = Sonda.objects.all()
                hostsservicessondas = HostsServicesSondas.objects.all()

                for sonda in sondas:
                    scripts[sonda.name] = {}

                for hostservicesonda in hostsservicessondas:

                    if not int(hostservicesonda.check_every/60) in scripts[sonda.name]:
                        scripts[sonda.name][int(hostservicesonda.check_every/60)] = []

                    if hostservicesonda.service.pluging:
                        snipet = scriptSnippet.replace("$2", hostservicesonda.service.command)
                        snipet = snipet.replace("$HOST", hostservicesonda.host.address)
                        snipet = snipet.replace("$SERVICE", hostservicesonda.service.name + "_" + hostservicesonda.sonda.name)
                        scripts[hostservicesonda.sonda.name][hostservicesonda.check_every].append(snipet)
                    else:
                        scripts[hostservicesonda.sonda.name][hostservicesonda.check_every].append(hostservicesonda.service.command.replace("$HOST", hostservicesonda.host.address))

                ## Render template

                f = open("templates/check_template.sh", "r")
                template = Template(f.read())
                f.close()

                for sonda in sondas:
                    script = open("scripts/checks-" + sonda.name + ".sh", "w")
                    script.write(template.render(Context({
                        "NSCA_CONF_FILE": "/etc/send_nsca.cfg",
                        "DIR_PLUGINGS": "/usr/lib/nagios/plugins",
                        "NAGIOS_SERVER": "193.145.118.253",
                        "checks": scripts[sonda.name].iteritems(),
                    })))
                    script.close()
                ## End Render

                ## Send Scripts
                crontabtemplate = 'echo "*/$2 * * * * root /root/$1 $2" >> /etc/crontab'
                for sonda in sondas:
                    print(sonda.address)
                    env.host_string = str(sonda.address)
                    env.key_filename = 'keys/id_rsa.pem'
                    put("scripts/checks-" + sonda.name + ".sh", "/root/" + "checks-" + sonda.name + ".sh")

                    for i in scripts[sonda.name].keys():
                        crontab = crontabtemplate.replace("$2", i)
                        run(crontab.replace("$1", "checks-" + sonda.name + ".sh "))

                    run("chmod +x /root/" + "checks-" + sonda.name + ".sh")


            except:
                c = {}
                c.update(csrf(request))
                c['status'] = "Unexpected error: \n"
                for fails in sys.exc_info()[0:5]:
                    c['status'] = c['status'] + "\n" + str(fails)
                response = render_to_response('index.html', c)
                return response

            c = {}
            c.update(csrf(request))
            c['status'] = "Configuraciones enviadas correctamente"
            c['HostsServicesSondas'] = HostsServicesSondas.objects.all()
            response = render_to_response('index.html', c)
            return response

        else:
            print ("get o post sin parametros usados")
            c = {}
            c.update(csrf(request))
            c['HostsServicesSondas'] = HostsServicesSondas.objects.all()
            response = render_to_response('index.html', c)
            return response

    def post(self, request, *args, **kwargs):
        return self.get(request, args, kwargs)


class NagiosCfg(APIView):

    def get(self, request, format=None):

        print ("Creando configuraciones nagios")

        ## Render template
        f = open("templates/nagioscfg_template.cfg", "r")
        template = Template(f.read())
        f.close()

        hostsservicessondas = HostsServicesSondas.objects.all()
        for x in hostsservicessondas:
            x.check_every = x.check_every * 2

        response = template.render(
            Context({
                "hosts": Host.objects.all(),
                "hostsservicessondas": hostsservicessondas,
            }))
        ## End Render
        return Response(response, status=httpstatus.HTTP_200_OK)

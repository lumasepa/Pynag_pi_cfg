from main.models import Host, Sonda, HostsServicesSondas
from django.views.generic import TemplateView
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from rest_framework.views import Response, APIView
from rest_framework import status as httpstatus
from django.template import Context
from tasks import send_nrpecfg
from Pynag_pi_cfg import settings

class Index(TemplateView):

    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        if request.GET.get('sendcfg', '') == "1" or request.POST.get('sendcfg', '') == "1":
            for sonda in Sonda.objects.all():
                send_nrpecfg.apply_async((sonda.pk, None), serializer="json")
                #send_nrpecfg(sonda.pk, None)

            c = {}
            c.update(csrf(request))
            c['status'] = "Configuraciones enviadas correctamente"
            c['HostsServicesSondas'] = HostsServicesSondas.objects.all()
            return render_to_response('index.html', c)

        else:
            print ("get o post sin parametros usados")
            c = {}
            c.update(csrf(request))
            c['HostsServicesSondas'] = HostsServicesSondas.objects.all()
            return render_to_response('index.html', c)

    def post(self, request, *args, **kwargs):
        return self.get(request, args, kwargs)


class NagiosCfg(APIView):

    def get(self, request, format=None):

        template = settings.PROJECT_ROOT + "/templates/nagioscfg_template.cfg"

        response = render_to_response(template,
                                      Context({
                                          "hosts": Host.objects.all(),
                                          "hostsservicessondas": HostsServicesSondas.objects.all(),
                                          "sondas": Sonda.objects.all(),
                                      }),
                                      mimetype="text/plain")
        response['Content-Disposition'] = 'attachment; filename=nagios.cfg'
        return response

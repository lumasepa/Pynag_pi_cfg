from django.shortcuts import render

# Create your views here.


from main.models import Services, Hosts, Sondas, HostsServicesSondas
from django.core import serializers
from django.shortcuts import HttpResponse
from rest_framework import Response

def services_list(request):
    data = serializers.serialize("yaml", Services.objects.all())
    print(data)
    return Response(data)


def hosts_list(request):
    data = serializers.serialize("yaml", Hosts.objects.all())
    return HttpResponse(data)


def sondas_list(request):
    data = serializers.serialize("yaml", Sondas.objects.all())
    return HttpResponse(data)


def hostsservicessondas_list(request):
    data = serializers.serialize("yaml", HostsServicesSondas.objects.all())
    return HttpResponse(data)
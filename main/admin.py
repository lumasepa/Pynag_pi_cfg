from django.contrib import admin

# Register your models here.

from main.models import Hosts, Services, Sondas, HostsServicesSondas
from django.contrib import admin


class HostsServicesSondasInline(admin.StackedInline):
    model = HostsServicesSondas
    extra = 2


class HostsAdmin(admin.ModelAdmin):
    inlines = [HostsServicesSondasInline]
    search_fields = ['name', 'address']
    list_display = ('name', 'address')
    pass


class ServicesAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name']
    pass


class SondasAdmin(admin.ModelAdmin):
    search_fields = ['name', 'address']
    list_display = ('name', 'address')
    pass

admin.site.register(Hosts, HostsAdmin)
admin.site.register(Services, ServicesAdmin)
admin.site.register(Sondas, SondasAdmin)

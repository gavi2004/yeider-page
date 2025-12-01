from django.contrib import admin
from .models import CosteEnvio

@admin.register(CosteEnvio)
class CosteEnvioAdmin(admin.ModelAdmin):
    list_display = ('destino', 'costo_adicional', 'descripcion')
    search_fields = ('destino__nombre',)
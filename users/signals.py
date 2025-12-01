from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Horario, Boleto, Paquete
import random

@receiver(post_save, sender=Horario)
def crear_boletos_automaticamente(sender, instance, created, **kwargs):
    if not created:
        return
        
    destino = instance.destino
    horario = instance

    if not Boleto.objects.filter(horario=horario).exists():
        boletos = []
        for i in range(100):  

            tipo = random.choices(['general', 'vip'], weights=[70, 30])[0]
            precio = destino.precio_vip if tipo == 'vip' else destino.precio_general
            
            boletos.append(Boleto(
                tipo=tipo,
                precio=precio,
                destino=destino,
                horario=horario,
                estado='libre'
            ))
        
        Boleto.objects.bulk_create(boletos)
        print(f"✅ {len(boletos)} boletos creados para {destino.nombre} - {horario.fecha} {horario.hora}")

@receiver(post_save, sender=Paquete)
def log_paquete_creation(sender, instance, created, **kwargs):
    if created:
        print(f"📦 Paquete creado: ID {instance.id} - {instance.tipo} para {instance.receptor}")
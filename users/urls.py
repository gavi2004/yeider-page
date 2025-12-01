from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('admi/', views.home_admin, name='home_admin'),
    path('home/empleado/', views.home_empleado, name='home_empleado'),
    path('home/cliente/', views.home_cliente, name='home_cliente'),
    path('login/', views.login, name='login'),
    path('register_user/', views.register, name='register'),
    path('edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('usuarios/eliminar/<int:user_id>/', views.delete_user, name='delete_user'),
    path('listar_users/', views.list_users, name='list_users'),
    path('logout/', views.logout, name='logout'),
    path('register_employer/', views.registrar_aspirante, name='register_aspirante'),
    path('boletos/', views.listar_boletos, name='listar_boletos'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('agregar/<int:boleto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('confirmar/', views.confirmar_compra, name='confirmar_compra'),
    path('destinos/', views.listar_destinos, name='list_destinos'),
    path('destinos/crear/', views.crear_destino, name='crear_destino'),
    path('destinos/editar/<int:pk>/', views.editar_destino, name='editar_destino'),
    path('destinos/eliminar/<int:pk>/', views.eliminar_destino, name='eliminar_destino'),
    path('destiny/', views.destiny_client, name='destiny'),
    path('destino/<int:destino_id>/', views.detalle_destino, name='detalle_destino'),
    path('pago/verificar/<int:pago_id>/', views.realizar_pago, name='verificar_pago'),
    path('destinos/', views.destiny_client, name='destiny_client'),
    path('destinos/<int:destino_id>/detalle/', views.ver_detalle_destino, name='ver_detalle_destino'),
    path('destino/<int:destino_id>/seleccionar/', views.seleccionar_boletos, name='seleccionar_boletos'),
    path('crear_horario/', views.crear_horario, name='crear_horario'),
    path('horarios/', views.listar_horarios, name='listar_horarios'),
    path('admi/gestionar-pagos/', views.gestionar_pagos, name='gestionar_pagos'),
    path('pago/', views.realizar_pago, name='realizar_pago'),
    path('historial-ventas/', views.historial_ventas, name='historial_ventas'),
    path('factura/<int:venta_id>/', views.factura, name='factura'),
    path('gestionar_aspirantes/', views.gestionar_aspirantes, name='gestionar_aspirantes'),
    path('enviar_paq/', views.enviar_paquete, name='enviar_paquete'),
    path('verificar-datos/', views.verificar_datos, name='verificar_datos'),
    path('horarios/editar/<int:horario_id>/', views.editar_horario, name='editar_horario'),
    path('horarios/eliminar/<int:horario_id>/', views.eliminar_horario, name='eliminar_horario'),
    path('mis_boletos/', views.mis_boletos, name='mis_boletos'),
    path('carrito/eliminar/<int:carrito_id>/', views.eliminar_boleto_carrito, name='eliminar_boleto'),
    path('carrito/vaciar/', views.vaciar_carrito, name='vaciar_carrito'),
    path('factura_pdf/<int:venta_id>/', views.factura_pdf, name='factura_pdf'),
    path('eliminar-paquete/<int:pk>/', views.eliminar_paquete_carrito, name='eliminar_paquete'),
    path('mis_paquetes/', views.mis_paquetes, name='mis_paquetes'),
    path('403/', views.error_403, name='error_403'),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
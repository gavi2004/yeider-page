from django.shortcuts import render, redirect, get_object_or_404
from .forms import UsuarioLoginForm, UsuarioRegistroForm, UsuarioEdicionForm, RegisterAspiranteForm, DestinoForm, PagoForm,HorarioForm,PaqueteForm
from .models import Usuario, Boleto, CarritoPaquetes,CarritoBoletos, Destino, Pago, Ventas, Reserva, Horario, Paquete
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.utils.timezone import now
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.http import Http404
import datetime
from django.contrib.admin.views.decorators import staff_member_required
from decimal import Decimal
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Q
from django.db.models import Count
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
import tempfile
import random
from django.db.models import Prefetch
from collections import Counter
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.safestring import mark_safe
from django.core.serializers.json import DjangoJSONEncoder


def index(request):

    destinos = Destino.objects.all()
    

    destinos_aleatorios = random.sample(list(destinos), 3) if len(destinos) >= 3 else destinos

    context = {
        'destinos': destinos_aleatorios
    }

    return render(request, 'users/index.html', context)


@login_required
def home(request):
    usuario_actual = request.user

    if usuario_actual.rol == 'empleado':
        return redirect('home_empleado')
    elif usuario_actual.rol == 'cliente':
        return redirect('home_cliente')
    elif usuario_actual.rol == 'admin':
        return redirect('home_admin')
    else:
        messages.error(request, "Tu rol no es válido.")
        return redirect('logout')

@login_required
def home_admin(request):
    if request.user.rol != 'admin':
        return render(request, 'users/error_403.html', status=403)  

    usuario_actual = request.user
    return render(request, 'users/home_admin.html', {
        'usuario_actual': usuario_actual,
    })


@login_required
def home_empleado(request):
    if request.user.rol != 'empleado':
        return render(request, 'users/error_403.html', status=403)  

    usuario_actual = request.user
    usuarios = Usuario.objects.all()  
    return render(request, 'users/home_empleado.html', {
        'usuario_actual': usuario_actual,
        'usuarios': usuarios,
    })

@login_required
def home_cliente(request):
    if request.user.rol != 'cliente':
        return render(request, 'users/error_403.html', status=403)  

    usuario_actual = request.user
    return render(request, 'users/home_cliente.html', {
        'usuario_actual': usuario_actual
    })


def login(request):
    if request.method == 'POST':
        form = UsuarioLoginForm(request.POST)
        if form.is_valid():
            usuario = form.cleaned_data['usuario']  
            auth_login(request, usuario)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Inicio de sesión exitoso.',
                    'redirect_url': 'home'  
                })
            else:
                messages.success(request, "Inicio de sesión exitoso.")
                return redirect('home')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = form.errors.get('__all__') or ['Correo o contraseña incorrectos.']
                return JsonResponse({
                    'success': False,
                    'message': errors[0]  
                })
            else:
                messages.error(request, "Correo o contraseña incorrectos.")
    else:
        form = UsuarioLoginForm()
    return render(request, 'users/login.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = UsuarioRegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario registrado con éxito.")
            return redirect('login')
        else:
            form_errors = form.errors.get_json_data()
            errors_json = json.dumps(form_errors, cls=DjangoJSONEncoder)
    else:
        form = UsuarioRegistroForm()
        errors_json = None

    return render(request, 'users/register_client.html', {
        'form': form,
        'form_errors': errors_json
    })



def registrar_aspirante(request):
    if request.method == 'POST':
        form = RegisterAspiranteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  
    else:
        form = RegisterAspiranteForm()
    
    return render(request, 'users/register_aspirante.html', {'form': form})


@login_required
def edit_user(request, user_id):
    rol_usuario = request.user.rol

    if rol_usuario not in ['empleado', 'admin']:
        return render(request, '403.html', status=403)
    
    usuario = get_object_or_404(Usuario, id=user_id)
    if request.method == 'POST':
        form = UsuarioEdicionForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado con éxito.")
            return redirect('list_users')
    else:
        form = UsuarioEdicionForm(instance=usuario)
    return render(request, 'users/edit_user.html', {'form': form, 'usuario': usuario})

@require_POST
@login_required
def delete_user(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    if request.user.id == usuario.id:
        messages.error(request, "No puedes eliminar tu propio usuario.")
        return redirect('home')

    usuario.delete()
    messages.success(request, "Usuario eliminado con éxito.")
    return redirect('list_users')



@login_required
def list_users(request):
    usuario_actual = request.user
    if usuario_actual.rol != 'admin':
        messages.warning(request, "No tienes permisos para ver esta página.")
        return redirect('home')

    query = request.GET.get('q', '')
    rol = request.GET.get('rol', '')

    usuarios = Usuario.objects.exclude(id=usuario_actual.id)

    if query:
        usuarios = usuarios.filter(
            Q(nombre__icontains=query) |
            Q(email__icontains=query) |
            Q(cedula__icontains=query) |
            Q(rol__icontains=query)
        )

    if rol:
        usuarios = usuarios.filter(rol=rol)

    usuarios = usuarios.order_by('id')


    from django.core.paginator import Paginator
    paginator = Paginator(usuarios, 10)  
    page_number = request.GET.get('page')
    usuarios_paginados = paginator.get_page(page_number)

    return render(request, 'users/list_users.html', {
        'usuarios': usuarios_paginados,
        'query': query,
        'rol': rol,
        'usuario_actual': usuario_actual,
    })


def logout(request):
    auth_logout(request)  
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect('index')






@login_required
def listar_boletos(request):
    boletos = Boleto.objects.all()
    return render(request, 'users/listar_boletos.html', {'boletos': boletos})

@login_required
def listar_destinos(request):
    rol_usuario = request.user.rol

    if rol_usuario not in ['admin', 'empleado']:
        return render(request, 'users/error_403.html', status=403)  

    destinos = Destino.objects.all()
    return render(request, 'users/list_destinos.html', {
        'destinos': destinos,
        'rol': rol_usuario,
    })


@login_required
def crear_destino(request):
    rol_usuario = request.user.rol
    errores_form = None

    if rol_usuario not in ['empleado', 'admin']:
        return render(request, 'users/error_403.html', status=403)  

    if request.method == 'POST':
        form = DestinoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Destino creado con éxito.")
            return redirect('list_destinos')
        else:
            errores_form = json.dumps([
                f"{form.fields[field].label}: {error}"
                for field, errors in form.errors.items()
                for error in errors
            ])
    else:
        form = DestinoForm()

    context = {
        'form': form,
        'rol': rol_usuario,
        'errores': mark_safe(errores_form) if errores_form else None,
    }
    return render(request, 'users/crear_destino.html', context)



def editar_destino(request, pk):
    destino = get_object_or_404(Destino, pk=pk)
    if request.method == 'POST':
        form = DestinoForm(request.POST, instance=destino)
        if form.is_valid():
            form.save()
            return redirect('list_destinos')

    else:
        form = DestinoForm(instance=destino)
    return render(request, 'users/editar_destino.html', {'form': form, 'accion': 'Editar'})


@login_required
def eliminar_destino(request, pk):
    destino = get_object_or_404(Destino, pk=pk)
    if request.method == 'POST':
        destino.delete()
        return redirect('list_destinos')
    return HttpResponseForbidden("Acción no permitida")



@login_required
def destiny_client(request):

    if request.user.rol != 'cliente':
        return render(request, '403.html', status=403)

    destinos = Destino.objects.all() 

    context = {
        'destinos': destinos
    }

    return render(request, 'users/destiny.html', context)

@login_required
def ver_detalle_destino(request, destino_id):
    destino = get_object_or_404(Destino, id=destino_id)
    boletos = Boleto.objects.filter(destino=destino, estado='libre')

    return render(request, 'users/detalle_destino.html', {
        'destino': destino,
        'boletos': boletos,
    })



@login_required
def seleccionar_boletos(request, destino_id):
    destino = get_object_or_404(Destino, id=destino_id)

    if request.method == "POST":
        cantidad = int(request.POST.get("cantidad"))
        horario_id = request.POST.get("horario_id")
        horario = get_object_or_404(Horario, id=horario_id)

        boletos_disponibles = Boleto.objects.filter(destino=destino, horario=horario, estado='libre')[:cantidad]

        if boletos_disponibles.count() < cantidad:
            return render(request, "detalle_destino.html", {
                "destino": destino,
                "horarios": destino.horarios.all(),
                "error": "No hay suficientes boletos disponibles para este horario."
            })


        carrito = CarritoBoletos.objects.create(
            usuario=request.user,
            destino=destino,
            cantidad=cantidad,
            horario=horario,
            total=sum(b.precio for b in boletos_disponibles)
        )


        for boleto in boletos_disponibles:
            boleto.estado = "carrito"
            boleto.save()
            carrito.boletos.add(boleto)


        destino.boletos_disponibles = Boleto.objects.filter(destino=destino, estado='libre').count()
        destino.save()

        return redirect("ver_carrito")

    return redirect("destiny_client")


@login_required
def realizar_pago(request):
    carritos_boletos = CarritoBoletos.objects.filter(usuario=request.user)
    carritos_paquetes = CarritoPaquetes.objects.filter(usuario=request.user)

    if not carritos_boletos.exists() and not carritos_paquetes.exists():
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('ver_carrito')

    total = Decimal('0')
    for carrito in carritos_boletos:
        total += carrito.calcular_total()
    for carrito in carritos_paquetes:
        total += carrito.calcular_total()

    if request.method == 'POST':
        form = PagoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                pago = form.save(commit=False)
                pago.usuario = request.user
                pago.monto = total
                pago.estado = 'pendiente'
                pago.save()


                venta = procesar_compra(request.user)
                
                messages.success(request, 'Pago realizado con éxito. Se ha generado tu factura.')
                return redirect('factura', venta_id=venta.id)
                
            except Exception as e:
                messages.error(request, f'Ocurrió un error al procesar el pago: {str(e)}')
        else:

            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PagoForm(initial={'monto': total})

    return render(request, 'users/formulario_pago.html', {
        'carritos_boletos': carritos_boletos,
        'carritos_paquetes': carritos_paquetes,
        'total': total,
        'form': form,
        'usuario_actual': request.user
    })

def boletos_disponibles(destino_id):
    return Boleto.objects.filter(destino_id=destino_id, estado='libre').count()





@login_required
def reservar_destino(request, destino_id):
    if request.method == 'POST' and request.user.rol == 'cliente':
        destino = get_object_or_404(Destino, id=destino_id)
        horario_id = request.POST.get('horario_id')

        horario = get_object_or_404(Horario, id=horario_id, destino=destino)


        Reserva.objects.create(
            usuario=request.user,
            destino=destino,
            horario=horario
        )

        return redirect('confirmacion_reserva')  

    return render(request, '403.html', status=403)



@login_required
def crear_horario(request):
    rol_usuario = request.user.rol

    if rol_usuario not in ['empleado', 'admin']:
        return render(request, '403.html', status=403)

    if request.method == 'POST':
        form = HorarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_horarios')  
    else:
        form = HorarioForm()
    
    return render(request, 'users/crear_horario.html', {
        'form': form,
        'rol': rol_usuario,
    })

@login_required
def listar_horarios(request):
    rol_usuario = request.user.rol

    if rol_usuario not in ['empleado', 'admin']:
        return render(request, 'users/error_403.html', status=403)  

    horarios = Horario.objects.all()
    return render(request, 'users/listar_horarios.html', {
        'horarios': horarios,
        'rol': rol_usuario,
    })


def error_403(request):
    return render(request, 'users/error_403.html')

@login_required
def detalle_destino(request, destino_id):
    destino = get_object_or_404(Destino, id=destino_id)
    horarios = Horario.objects.filter(destino=destino).prefetch_related(
        Prefetch('boletos', queryset=Boleto.objects.filter(estado='libre'))
    )

    if request.method == "POST":
        try:
            cantidad = int(request.POST.get('cantidad', 1))
            tipo_boleto = request.POST.get('tipo_boleto')
            horario_id = request.POST.get('horario')
            
            if cantidad < 1:
                raise ValueError("La cantidad debe ser al menos 1")

            horario = get_object_or_404(Horario, id=horario_id, destino=destino)
            

            boletos_disponibles = list(Boleto.objects.filter(
                destino=destino,
                horario=horario,
                tipo=tipo_boleto,
                estado='libre'
            )[:cantidad])

            if len(boletos_disponibles) < cantidad:
                messages.error(request, 
                    f"No hay suficientes boletos {tipo_boleto}. "
                    f"Disponibles: {len(boletos_disponibles)}, "
                    f"Se solicitaron: {cantidad}"
                )
                return redirect('detalle_destino', destino_id=destino.id)

            carrito, created = CarritoBoletos.objects.get_or_create(
                usuario=request.user,
                destino=destino,
                horario=horario,
                defaults={'cantidad': cantidad}
            )
            
            if not created:
                carrito.cantidad += cantidad
                carrito.save()

            for boleto in boletos_disponibles:
                boleto.estado = 'carrito'
                boleto.save()
                carrito.boletos.add(boleto)

            carrito.actualizar_total()
            messages.success(request, f"✅ {cantidad} boleto(s) {tipo_boleto} agregados al carrito")
            return redirect('ver_carrito')

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('detalle_destino', destino_id=destino.id)

    return render(request, 'users/detalle_destino.html', {
        'destino': destino,
        'horarios': horarios,
    })


def calcular_monto(request=None):
    if request:
        total_enviado = request.POST.get('total')
        try:
            return float(total_enviado)
        except (TypeError, ValueError):
            return 0.0  
    return 0.0

@login_required
def gestionar_pagos(request):
    if request.user.rol != 'admin':
        return redirect('home')

    pagos = Pago.objects.filter(estado='pendiente').select_related('usuario')

    if request.method == 'POST':
        pago_id = request.POST.get('pago_id')
        accion = request.POST.get('accion')

        try:
            pago = Pago.objects.get(id=pago_id)

            if accion == 'aprobar':
                pago.estado = 'aprobado'
                pago.fecha_verificacion = timezone.now()
                pago.save()

                venta = procesar_compra(pago.usuario)
                messages.success(request, f'Pago aprobado y compra confirmada por ${venta.total_pagado:.2f}.')

            elif accion == 'rechazar':
                pago.estado = 'rechazado'
                pago.fecha_verificacion = timezone.now()
                pago.save()
                messages.info(request, 'Pago rechazado.')

            return redirect('gestionar_pagos')

        except Pago.DoesNotExist:
            messages.error(request, 'Pago no encontrado.')
        except ValueError as e:
            messages.error(request, f'Error al procesar la compra: {e}')

    return render(request, 'users/gestionar_pagos.html', {'pagos': pagos})



@login_required
def historial_ventas(request):
    if request.user.rol == 'admin':
        ventas = Ventas.objects.all().prefetch_related('boletos', 'paquetes').order_by('-fecha_compra')
    else:
        ventas = Ventas.objects.filter(usuario=request.user).prefetch_related('boletos', 'paquetes').order_by('-fecha_compra')

    query = request.GET.get('q', '')
    tipo = request.GET.get('tipo', '')

    if query:
        ventas = ventas.filter(
            Q(fecha_compra__icontains=query) |
            Q(destino__nombre__icontains=query) |
            Q(cantidad__icontains=query) |
            Q(total_pagado__icontains=query) |
            Q(hora__icontains=query) |
            Q(usuario__nombre__icontains=query) |
            Q(usuario__cedula__icontains=query)
        )

    if tipo:
        if tipo == 'boletos':
            ventas = ventas.filter(boletos__isnull=False, paquetes__isnull=True)
        elif tipo == 'paquetes':
            ventas = ventas.filter(paquetes__isnull=False, boletos__isnull=True)
        elif tipo == 'mixta':
            ventas = ventas.filter(boletos__isnull=False, paquetes__isnull=False)


    paginator = Paginator(ventas, 10)
    page = request.GET.get('page')

    try:
        ventas_paginator = paginator.page(page)
    except PageNotAnInteger:
        ventas_paginator = paginator.page(1)
    except EmptyPage:
        ventas_paginator = paginator.page(paginator.num_pages)


    total_boletos = 0
    total_paquetes = 0
    ventas_mixtas = 0

    for venta in ventas_paginator:
        num_boletos = venta.boletos.count()
        num_paquetes = venta.paquetes.count()
        total_boletos += num_boletos
        total_paquetes += num_paquetes

        if num_boletos > 0 and num_paquetes > 0:
            ventas_mixtas += 1


    ventas_total = Ventas.objects.all().prefetch_related('boletos', 'paquetes')
    total_boletos_general = 0
    total_paquetes_general = 0
    ventas_mixtas_general = 0

    for venta in ventas_total:
        num_boletos = venta.boletos.count()
        num_paquetes = venta.paquetes.count()
        total_boletos_general += num_boletos
        total_paquetes_general += num_paquetes

        if num_boletos > 0 and num_paquetes > 0:
            ventas_mixtas_general += 1

    return render(request, 'users/historial_ventas.html', {
        'ventas': ventas_paginator,
        'total_boletos': total_boletos,
        'total_paquetes': total_paquetes,
        'ventas_mixtas': ventas_mixtas,
        'query': query,
        'tipo': tipo,


        'total_boletos_general': total_boletos_general,
        'total_paquetes_general': total_paquetes_general,
        'ventas_mixtas_general': ventas_mixtas_general,
        'ventas_total_count': ventas_total.count(),
    })


@login_required
def factura(request, venta_id):
    venta = get_object_or_404(Ventas, id=venta_id, usuario=request.user)
    
    items = []
    primer_paquete = None  

    num_boletos = venta.boletos.count()
    num_paquetes = venta.paquetes.count()


    if num_boletos > 0 and num_paquetes > 0:
        tipo_venta = 'mixta'
    elif num_boletos > 0:
        tipo_venta = 'boletos'
    elif num_paquetes > 0:
        tipo_venta = 'paquetes'
    else:
        tipo_venta = 'vacía'  


    for boleto in venta.boletos.select_related('destino', 'horario'):
        items.append({
            'tipo': 'boleto',
            'descripcion': f"Boleto {boleto.get_tipo_display()} a {boleto.destino.nombre}",
            'detalle': f"{boleto.horario.fecha} a las {boleto.horario.hora}",
            'precio': boleto.precio,
            'cantidad': 1
        })


    for i, paquete in enumerate(venta.paquetes.select_related('destino')):
        items.append({
            'tipo': 'paquete',
            'descripcion': f"Paquete {paquete.get_tipo_display()}",
            'detalle': f"Peso: {paquete.peso} kg - {paquete.descripcion}",
            'precio': paquete.precio_envio,
            'cantidad': 1
        })
        if i == 0:
            primer_paquete = paquete  

    total = sum(item['precio'] for item in items)

    context = {
        'venta': venta,
        'usuario_actual': request.user,
        'cliente': venta.usuario,
        'items': items,
        'total': total,
        'fecha_compra': venta.fecha_compra.strftime("%d/%m/%Y %H:%M"),
        'tipo_venta': tipo_venta,
        'paquete': primer_paquete,  
    }

    return render(request, 'users/factura.html', context)

@login_required
def gestionar_aspirantes(request):
    if request.user.rol != 'admin':
        return HttpResponseForbidden("No tienes permisos para acceder a esta página.")

    aspirantes = Usuario.objects.filter(rol='aspirante')

    if request.method == 'POST':
        user_id = request.POST.get('usuario_id')
        accion = request.POST.get('accion')
        usuario = get_object_or_404(Usuario, id=user_id, rol='aspirante')

        if accion == 'aceptar':
            usuario.rol = 'empleado'  
            usuario.save()
            messages.success(request, f"Aspirante {usuario.nombre} ha sido aceptado.")
        elif accion == 'rechazar':
            usuario.delete()
            messages.success(request, "Aspirante rechazado y eliminado del sistema.")
        return redirect('gestionar_aspirantes')

    return render(request, 'users/gestionar_aspirantes.html', {
        'aspirantes': aspirantes
    })



@csrf_exempt
def verificar_datos(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        cedula = data.get('cedula')
        telefono = data.get('telefono')
        email = data.get('email')

        existe = Usuario.objects.filter(cedula=cedula).exists() or \
                 Usuario.objects.filter(telefono=telefono).exists() or \
                 Usuario.objects.filter(email=email).exists()

        return JsonResponse({'existe': existe})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


def editar_horario(request, horario_id):
    horario = get_object_or_404(Horario, id=horario_id)

    if request.method == 'POST':
        form = HorarioForm(request.POST, instance=horario)
        if form.is_valid():
            form.save()
            return redirect('listar_horarios') 
    else:
        form = HorarioForm(instance=horario)

    return render(request, 'users/editar_horario.html', {
        'form': form,
        'horario': horario
    })

@require_POST
def eliminar_horario(request, horario_id):
    horario = get_object_or_404(Horario, id=horario_id)
    horario.delete()
    return redirect('listar_horarios')


@login_required
def mis_boletos(request):
    boletos = Boleto.objects.filter(
        usuario=request.user,
        estado__in=['carrito', 'vendido']
    )

    resumen = boletos.values('tipo', 'estado', 'precio').annotate(cantidad=Count('id'))

    return render(request, 'users/mis_boletos.html', {
        'resumen': resumen,
    })


@login_required
def mis_paquetes(request):
    paquetes = Paquete.objects.filter(
        remitente=request.user,
        estado__in=['carrito', 'vendido']
    )

    resumen = paquetes.values('tipo', 'estado', 'precio_envio').annotate(cantidad=Count('id'))

    return render(request, 'users/mis_paquetes.html', {
        'resumen': resumen,
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def verificar_pago(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id, estado='pendiente')

    pago.estado = 'verificado'
    pago.fecha_verificacion = timezone.now()
    pago.save()


    total = procesar_compra(pago.usuario)

    messages.success(request, f'Pago verificado y compra registrada para {pago.usuario.email}')
    return redirect('panel_pagos')

@login_required
def estado_pago(request):
    pagos = Pago.objects.filter(usuario=request.user).order_by('-fecha_registro')
    return render(request, 'users/estado_pago.html', {'pagos': pagos})



def procesar_compra(usuario):
    carritos_boletos = CarritoBoletos.objects.filter(usuario=usuario)
    carritos_paquetes = CarritoPaquetes.objects.filter(usuario=usuario)

    total = Decimal('0')
    boletos_finales = []
    paquetes_finales = []


    destino = (
        carritos_boletos.first().destino if carritos_boletos.exists()
        else carritos_paquetes.first().destino if carritos_paquetes.exists()
        else None
    )


    for carrito in carritos_boletos:
        boletos = list(carrito.boletos.all())
        for boleto in boletos:
            boleto.estado = 'vendido'
            boleto.usuario = usuario
            boleto.save()
            boletos_finales.append(boleto)
            total += boleto.precio
        carrito.delete()


    for carrito in carritos_paquetes:
        paquetes = list(carrito.paquetes.all())
        for paquete in paquetes:
            paquete.estado = 'vendido'
            paquete.save()
            paquetes_finales.append(paquete)
            total += paquete.precio_envio
        carrito.delete()


    if not boletos_finales and not paquetes_finales:
        raise ValueError("No hay productos para procesar.")

    venta = Ventas.objects.create(
        usuario=usuario,
        destino=destino,
        cantidad=len(boletos_finales) + len(paquetes_finales),
        hora=timezone.now().time(),
        total_pagado=total,
    )

    if boletos_finales:
        venta.boletos.set(boletos_finales)
    if paquetes_finales:
        venta.paquetes.set(paquetes_finales)

    return venta

@login_required
def vaciar_carrito(request):
  
    carritos_boletos = CarritoBoletos.objects.filter(usuario=request.user)
    for carrito in carritos_boletos:
        for boleto in carrito.boletos.all():
            boleto.estado = 'libre'
            boleto.save()
        carrito.delete()


    carritos_paquetes = CarritoPaquetes.objects.filter(usuario=request.user)
    for carrito in carritos_paquetes:
        for paquete in carrito.paquetes.all():
            paquete.estado = 'libre'
            paquete.save()
        carrito.delete()

    messages.success(request, "Carrito vaciado correctamente.")
    return redirect('ver_carrito')




@login_required
def factura_pdf(request, venta_id):
    venta = get_object_or_404(Ventas, id=venta_id)

    items = []

    for boleto in venta.boletos.all():
        items.append({
            'cantidad': 1,
            'tipo': 'boleto',
            'descripcion': f"Boleto a {venta.destino.nombre if venta.destino else 'Destino no especificado'}",
            'detalle': f"Horario: {venta.hora.strftime('%H:%M')}",
            'precio': boleto.precio
        })

    for paquete in venta.paquetes.all():
        items.append({
            'cantidad': 1,
            'tipo': 'paquete',
            'descripcion': f"Paquete hacia {venta.destino.nombre if venta.destino else 'Destino no especificado'}",
            'detalle': f"Peso: {paquete.peso} kg",
            'precio': paquete.precio_envio
        })

    html_string = render_to_string('users/factura_template.html', {
        'venta': venta,
        'usuario': venta.usuario,
        'cliente': venta.usuario,  
        'items': items,
        'total': venta.total_pagado,
    })

    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    result = html.write_pdf()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=factura_{venta.id}.pdf'

    response.write(result)

    return response




@login_required
def ver_carrito(request):

    carrito_boletos = CarritoBoletos.objects.filter(
        usuario=request.user
    ).select_related('destino', 'horario').prefetch_related('boletos')
    

    carrito_paquetes = CarritoPaquetes.objects.filter(
        usuario=request.user
    ).select_related('destino').prefetch_related('paquetes')
    

    total_boletos = sum(carrito.calcular_total() for carrito in carrito_boletos)
    total_paquetes = sum(carrito.calcular_total() for carrito in carrito_paquetes)
    total = total_boletos + total_paquetes
    

    carrito_items = []
    for carrito in carrito_boletos:
        carrito_items.append({
            'id': carrito.id,
            'destino': carrito.destino,
            'horario': carrito.horario,
            'cantidad': carrito.cantidad,
            'subtotal': carrito.total
        })
    
    paquetes = []
    for carrito in carrito_paquetes:
        for paquete in carrito.paquetes.all():
            paquetes.append(paquete)
    
    request.session['total_carrito'] = float(total)
    
    return render(request, 'users/ver_carrito.html', {
        'carrito_items': carrito_items,  
        'paquetes': paquetes,           
        'total_boletos': total_boletos,
        'total_paquetes': total_paquetes,
        'total': total,
    })


@login_required
def enviar_paquete(request):
    if request.method == 'POST':
        form = PaqueteForm(request.POST)
        if form.is_valid():
            paquete = form.save(commit=False)
            paquete.remitente = request.user
            paquete.estado = 'carrito'
            paquete.save()

  
            carrito, created = CarritoPaquetes.objects.get_or_create(
                usuario=request.user,
                destino=paquete.destino
            )
            
            carrito.paquetes.add(paquete)
            carrito.actualizar_total()
            
            messages.success(request, "Paquete agregado al carrito correctamente.")
            return redirect('ver_carrito')
    else:
        form = PaqueteForm()
    return render(request, 'users/enviar_paquete.html', {'form': form})


@login_required
@require_POST
def agregar_al_carrito(request, destino_id):
    destino = get_object_or_404(Destino, id=destino_id)
    cantidad = int(request.POST.get('cantidad', 1))
    horario_id = request.POST.get('horario_id')
    horario = get_object_or_404(Horario, id=horario_id)

    if destino.boletos_disponibles < cantidad:
        messages.error(request, "No hay suficientes boletos disponibles.")
        return redirect('listar_boletos')


    boletos_libres = Boleto.objects.filter(
        destino=destino, 
        horario=horario,
        estado='libre'
    )[:cantidad]

    if boletos_libres.count() < cantidad:
        messages.error(request, "No hay suficientes boletos disponibles para este horario.")
        return redirect('detalle_destino', destino_id=destino.id)


    carrito, created = CarritoBoletos.objects.get_or_create(
        usuario=request.user,
        destino=destino,
        horario=horario,
        defaults={'cantidad': cantidad}
    )
    
    if not created:
        carrito.cantidad += cantidad
        carrito.save()


    for boleto in boletos_libres:
        boleto.estado = 'carrito'
        boleto.save()
        carrito.boletos.add(boleto)

    carrito.actualizar_total()
    messages.success(request, "Boleto(s) agregado(s) al carrito.")
    return redirect('ver_carrito')


@login_required
def confirmar_compra(request):

    carritos_boletos = CarritoBoletos.objects.filter(usuario=request.user)
    total = Decimal('0')
    
    for carrito in carritos_boletos:
        boletos = carrito.boletos.all()
        subtotal = Decimal('0')
        
        for boleto in boletos:
            subtotal += boleto.precio
            boleto.estado = 'vendido'
            boleto.usuario = request.user
            boleto.save()

        Ventas.objects.create(
            usuario=request.user,
            destino=carrito.destino,
            cantidad=carrito.cantidad,
            hora=carrito.horario.hora,
            total_pagado=subtotal,
        )
        total += subtotal
        carrito.delete()


    carritos_paquetes = CarritoPaquetes.objects.filter(usuario=request.user)
    
    for carrito in carritos_paquetes:
        for paquete in carrito.paquetes.all():
            paquete.estado = 'vendido'
            paquete.save()
            
            Ventas.objects.create(
                usuario=request.user,
                destino=carrito.destino,
                cantidad=1,
                hora=timezone.now().time(),
                total_pagado=paquete.precio_envio,
                paquete=paquete
            )
            total += paquete.precio_envio
        carrito.delete()

    request.session['total_compra'] = str(total)
    messages.success(request, f"Compra confirmada. Total a pagar: ${total:.2f}")
    return redirect('realizar_pago')



@login_required
def eliminar_boleto_carrito(request, carrito_id):
    carrito = get_object_or_404(CarritoBoletos, id=carrito_id, usuario=request.user)
    

    for boleto in carrito.boletos.all():
        boleto.estado = 'libre'
        boleto.save()
    
    carrito.delete()
    messages.success(request, "Boletos eliminados del carrito.")
    return redirect('ver_carrito')



@login_required
@require_POST
def eliminar_paquete_carrito(request, pk):
    paquete = get_object_or_404(Paquete, id=pk, remitente=request.user)
    carrito = CarritoPaquetes.objects.filter(usuario=request.user, paquetes=paquete).first()
    
    if carrito:
        carrito.paquetes.remove(paquete)
        if carrito.paquetes.count() == 0:
            carrito.delete()
        else:
            carrito.actualizar_total()
    
    paquete.delete()
    messages.success(request, "Paquete eliminado del carrito")
    return redirect('ver_carrito')
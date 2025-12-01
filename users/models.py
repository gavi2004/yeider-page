from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UsuarioManager
from django.utils import timezone
from django.conf import settings

class Usuario(AbstractBaseUser, PermissionsMixin):
    ROLES = [
        ('cliente', 'Cliente'),
        ('aspirante', 'Aspirante'),
        ('empleado', 'Empleado'),
        ('admin', 'Administrador'),
    ]

    cedula = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15)
    rol = models.CharField(max_length=10, choices=ROLES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'cedula', 'telefono', 'rol']

    def __str__(self):
        return f"{self.nombre} ({self.rol})"


class Destino(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    transporte = models.CharField(
        max_length=10,
        choices=[('aereo', 'Aéreo'), ('maritimo', 'Marítimo')],
        default='aereo'
    )
    imagen = models.ImageField(upload_to='destinos/', null=True, blank=True)
    precio_general = models.DecimalField(max_digits=10, decimal_places=2, default=0)  
    precio_vip = models.DecimalField(max_digits=10, decimal_places=2, default=0)  
    

    precio_base_envio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10,
        help_text="Precio base para envío de paquetes a este destino"
    )
    precio_por_kilo_extra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=2,
        help_text="Precio por cada kilo adicional después del peso base"
    )
    peso_base = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=10,
        help_text="Peso base en kg para el cálculo del envío"
    )

    @property
    def boletos_disponibles(self):
        return Boleto.objects.filter(destino=self, estado='libre').count()

    def __str__(self):
        return f"{self.nombre} - {self.get_transporte_display()}"


class Horario(models.Model):
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE, related_name='horarios')
    fecha = models.DateField()
    hora = models.TimeField()

    def __str__(self):
        return f"{self.destino.nombre} - {self.fecha} {self.hora.strftime('%H:%M')}"
    
class Boleto(models.Model):
    TIPO_CHOICES = [
        ('general', 'General'),
        ('vip', 'VIP'),
    ]

    ESTADO_CHOICES = [
        ('libre', 'Libre'),
        ('carrito', 'En carrito'),
        ('vendido', 'Vendido'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    precio = models.DecimalField(max_digits=6, decimal_places=2)
    destino = models.ForeignKey('Destino', on_delete=models.CASCADE, related_name='boletos')
    horario = models.ForeignKey('Horario', on_delete=models.CASCADE, related_name='boletos')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='libre')


    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='boletos'
    )

    def __str__(self):
        return f"{self.get_tipo_display()} a {self.destino.nombre} - {self.horario.fecha} {self.horario.hora} - ${self.precio}"

    def save(self, *args, **kwargs):
        if not self.pk:
            print("🚨 Boleto creado:", self, flush=True)
        else:
            print("✏️ Boleto modificado:", self, flush=True)
        super().save(*args, **kwargs)





class CarritoBoletos(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE)
    horario = models.ForeignKey('Horario', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    boletos = models.ManyToManyField('Boleto', blank=True)

    def calcular_total(self):
        return sum(boleto.precio for boleto in self.boletos.all())

    def actualizar_total(self):
        self.total = self.calcular_total()
        self.save()

    def __str__(self):
        return f"{self.usuario.nombre} - {self.cantidad} boleto(s) a {self.destino.nombre}"

class CarritoPaquetes(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    paquetes = models.ManyToManyField('Paquete', blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calcular_total(self):
        return sum(paquete.precio_envio for paquete in self.paquetes.all())

    def actualizar_total(self):
        self.total = self.calcular_total()
        self.save()

    def __str__(self):
        return f"{self.usuario.nombre} - {self.paquetes.count()} paquete(s) a {self.destino.nombre}"

class Ventas(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    hora = models.TimeField(default=timezone.now)
    fecha_compra = models.DateTimeField(auto_now_add=True)
    total_pagado = models.DecimalField(max_digits=10, decimal_places=2)

    boletos = models.ManyToManyField(Boleto, blank=True)
    paquetes = models.ManyToManyField('Paquete', blank=True)  

    def __str__(self):
        items = []
        if self.boletos.exists():
            items.append(f"{self.boletos.count()} boleto(s)")
        if self.paquetes.exists():
            items.append(f"{self.paquetes.count()} paquete(s)")
        return f"{self.usuario.nombre} compró {' y '.join(items)} a {self.destino.nombre} por ${self.total_pagado}"


class Pago(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    METODOS_PAGO = [
        ('pmovil', 'Pago Móvil'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    metodo = models.CharField(max_length=20, choices=METODOS_PAGO, default='pmovil')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)

    referencia = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Número de referencia del pago móvil"
    )
    numero_tarjeta = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Campo sin uso para Pago Móvil"
    )
    observaciones = models.TextField(blank=True, null=True)
    comprobante = models.ImageField(upload_to='comprobantes/', blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='pendiente')
    fecha_verificacion = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.usuario.nombre} pagó ${self.monto} ({self.get_metodo_display()}) - Estado: {self.estado}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.referencia:
            raise ValidationError("Debe ingresar una referencia para el pago móvil.")



class Reserva(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE)
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE)
    fecha_reserva = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reserva de {self.usuario.nombre} para {self.destino.nombre} el {self.horario.fecha} a las {self.horario.hora}"


class Paquete(models.Model):
    ESTADOS = [
        ('carrito', 'En carrito'),
        ('vendido', 'Vendido'),
    ]

    TIPOS = [
        ('electronica', 'Electrónica'),
        ('ropa', 'Ropa'),
        ('maquinaria', 'Maquinaria'),
        ('otros', 'Otros'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPOS)
    peso = models.DecimalField(max_digits=6, decimal_places=2)
    descripcion = models.TextField()
    destino = models.ForeignKey('Destino', on_delete=models.CASCADE)
    remitente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='paquetes_enviados')
    receptor = models.CharField(max_length=100)
    fecha_envio = models.DateTimeField(auto_now_add=True)
    precio_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='carrito')

    def save(self, *args, **kwargs):

        base_price = 10  
        

        if self.peso > 10:
            self.precio_envio = base_price + (self.peso - 10) * 2
        else:
            self.precio_envio = base_price


        try:

            costo_destino = CosteEnvio.objects.get(destino=self.destino)
            self.precio_envio += costo_destino.costo_adicional
        except CosteEnvio.DoesNotExist:
            pass

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo} para {self.receptor}"


class CosteEnvio(models.Model):
    destino = models.OneToOneField(Destino, on_delete=models.CASCADE, related_name='coste_envio')
    costo_adicional = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        help_text="Costo adicional que se sumará al precio base del envío para este destino"
    )
    descripcion = models.CharField(
        max_length=255,
        blank=True,
        help_text="Descripción opcional del costo adicional"
    )

    def __str__(self):
        return f"Costo adicional para {self.destino.nombre}: ${self.costo_adicional}"
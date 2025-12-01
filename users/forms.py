from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from .models import Usuario,Destino,Pago,Horario,Paquete,Boleto
from django.forms import modelformset_factory
import re
from django.contrib.auth import get_user_model

class UsuarioRegistroForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput
    )
    confirmar_password = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput
    )

    class Meta:
        model = Usuario
        fields = ['cedula', 'nombre', 'email', 'telefono', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        allowed_domains = ['@gmail.com', '@proton.me', '@outlook.com']
        if not any(email.endswith(domain) for domain in allowed_domains):
            raise ValidationError("Solo se permiten correos de Gmail, Proton o Outlook.")
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError("Ya existe un usuario con este correo electrónico.")
        return email

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if not cedula.isdigit() or len(cedula) != 8:
            raise ValidationError("La cédula debe tener exactamente 8 dígitos numéricos.")
        if Usuario.objects.filter(cedula=cedula).exists():
            raise ValidationError("Ya existe un usuario con esta cédula.")
        return cedula

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if not telefono.isdigit() or len(telefono) != 11:
            raise ValidationError("El teléfono debe contener exactamente 11 dígitos numéricos.")
        if Usuario.objects.filter(telefono=telefono).exists():
            raise ValidationError("Ya existe un usuario con este número de teléfono.")
        return telefono

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if len(nombre.split()) < 2:
            raise ValidationError("Debe ingresar al menos nombre y apellido.")
        return nombre

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmar = cleaned_data.get("confirmar_password")

        if password and confirmar and password != confirmar:
            raise ValidationError("Las contraseñas no coinciden.")

        if password:
            if not any(char.isupper() for char in password):
                raise ValidationError("La contraseña debe contener al menos una letra mayúscula.")
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValidationError("La contraseña debe contener al menos un carácter especial.")

        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        password = self.cleaned_data["password"]
        usuario.set_password(password)
        usuario.rol = 'cliente'   
        if commit:
            usuario.save()
        return usuario

class RegisterAspiranteForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput
    )
    confirmar_password = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput
    )

    class Meta:
        model = Usuario
        fields = ['cedula', 'nombre', 'email', 'telefono', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        allowed_domains = ['@gmail.com', '@proton.me', '@outlook.com']
        if not any(email.endswith(domain) for domain in allowed_domains):
            raise ValidationError("Solo se permiten correos de Gmail, Proton o Outlook.")
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError("Ya existe un usuario con este correo electrónico.")
        return email

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if not cedula.isdigit() or len(cedula) != 8:
            raise ValidationError("La cédula debe tener exactamente 8 dígitos numéricos.")
        return cedula

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if not telefono.isdigit() or len(telefono) != 11:
            raise ValidationError("El teléfono debe contener exactamente 11 dígitos numéricos.")
        return telefono

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if len(nombre.split()) < 2:
            raise ValidationError("Debe ingresar al menos nombre y apellido.")
        return nombre

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmar = cleaned_data.get("confirmar_password")

        if password and confirmar and password != confirmar:
            raise ValidationError("Las contraseñas no coinciden.")

        if password:
            if not any(char.isupper() for char in password):
                raise ValidationError("La contraseña debe contener al menos una letra mayúscula.")
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValidationError("La contraseña debe contener al menos un carácter especial.")

        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        password = self.cleaned_data["password"]
        usuario.set_password(password)
        usuario.rol = 'aspirante'
        if commit:
            usuario.save()
        return usuario


class UsuarioEdicionForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Contraseña (opcional)',
        required=False,
        help_text='Deja este campo vacío si no deseas cambiar la contraseña.'
    )

    class Meta:
        model = Usuario
        fields = ['cedula', 'nombre', 'email', 'telefono', 'rol', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
     
        self.fields['cedula'].disabled = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un usuario con este correo electrónico.")

    
        allowed_domains = ['gmail.com', 'outlook.com', 'protonmail.com']
        domain = email.split('@')[-1]
        if domain not in allowed_domains:
            raise ValidationError("Solo se permiten correos de Gmail, Outlook o ProtonMail.")
        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        nueva_contraseña = self.cleaned_data.get('password')
        if nueva_contraseña:
            usuario.set_password(nueva_contraseña)
        if commit:
            usuario.save()
        return usuario


class UsuarioLoginForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico')
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        User = get_user_model()

        try:
            usuario = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("Usuario no encontrado.")

        
        if not usuario.check_password(password):
            raise forms.ValidationError("Contraseña incorrecta.")

        cleaned_data['usuario'] = usuario
        return cleaned_data


class UsuarioEliminacionForm(forms.Form):
    confirmacion = forms.BooleanField(label="Confirmo que deseo eliminar este usuario")




class DestinoForm(forms.ModelForm):
    class Meta:
        model = Destino
        fields = ['nombre', 'descripcion', 'transporte', 'imagen', 'precio_general', 'precio_vip']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'precio_general': forms.NumberInput(attrs={'step': '0.01'}),
            'precio_vip': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if Destino.objects.filter(nombre__iexact=nombre).exists():
            raise ValidationError('Ya existe un destino con este nombre.')
        return nombre



class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horario
        fields = ['destino', 'fecha', 'hora']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['destino'].queryset = Destino.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        destino = cleaned_data.get('destino')
        fecha = cleaned_data.get('fecha')
        hora = cleaned_data.get('hora')

        if destino and fecha and hora:
            qs = Horario.objects.filter(destino=destino, fecha=fecha, hora=hora)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("Ya existe un horario con este destino, fecha y hora.")
        
        return cleaned_data



class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['metodo', 'monto', 'referencia', 'numero_tarjeta', 'observaciones', 'comprobante']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

       
        self.fields['monto'].widget.attrs.update({
            'readonly': 'readonly',
            'class': 'form-control'
        })

class PaqueteForm(forms.ModelForm):
    class Meta:
        model = Paquete
        fields = ['tipo', 'peso', 'descripcion', 'destino', 'receptor']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'destino': forms.Select(attrs={'class': 'form-control'}),
            'receptor': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['destino'].queryset = Destino.objects.all()

class BoletoForm(forms.Form):
    tipo = forms.ChoiceField(choices=Boleto.TIPO_CHOICES)
    precio = forms.DecimalField(max_digits=6, decimal_places=2)
    cantidad = forms.IntegerField()
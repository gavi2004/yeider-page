"""Utility script to create regular users for the custom Usuario model.

Usage:
    python user.py run [--email EMAIL --nombre NOMBRE --cedula CEDULA --telefono TELEFONO \
                       --password PASSWORD --rol ROL]

Si omites los argumentos, se usarán los valores por defecto definidos en este archivo
para crear el usuario solicitado.
"""

import argparse
import os
import sys

import django
from django.core.exceptions import ValidationError

DEFAULT_USER_DATA = {
    "email": os.environ.get("USER_DEFAULT_EMAIL", "cliente@example.com"),
    "nombre": os.environ.get("USER_DEFAULT_NOMBRE", "Cliente Demo"),
    "cedula": os.environ.get("USER_DEFAULT_CEDULA", "00000000"),
    "telefono": os.environ.get("USER_DEFAULT_TELEFONO", "0000000000"),
    "rol": os.environ.get("USER_DEFAULT_ROL", "cliente"),
}

DEFAULT_PASSWORD = os.environ.get("USER_DEFAULT_PASSWORD", "changeme123")


def bootstrap_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proyecto.settings")
    try:
        django.setup()
    except Exception as exc:  # pragma: no cover - defensive
        print(f"No se pudo iniciar Django: {exc}", file=sys.stderr)
        sys.exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Crear un usuario regular")
    parser.add_argument("command", choices=["run"], help="Acción a realizar")
    parser.add_argument("--email", dest="email", help="Correo del usuario")
    parser.add_argument("--nombre", dest="nombre", help="Nombre completo")
    parser.add_argument("--cedula", dest="cedula", help="Cédula")
    parser.add_argument("--telefono", dest="telefono", help="Teléfono")
    parser.add_argument("--password", dest="password", help="Contraseña del usuario")
    parser.add_argument("--rol", dest="rol", help="Rol del usuario (cliente/aspirante/empleado/admin)")
    return parser.parse_args()


def run():
    args = parse_arguments()
    if args.command != "run":
        print("Comando no soportado", file=sys.stderr)
        sys.exit(1)

    bootstrap_django()

    from users.models import Usuario

    role_codes = {code for code, _ in Usuario.ROLES}

    email = args.email or DEFAULT_USER_DATA["email"]
    nombre = args.nombre or DEFAULT_USER_DATA["nombre"]
    cedula = args.cedula or DEFAULT_USER_DATA["cedula"]
    telefono = args.telefono or DEFAULT_USER_DATA["telefono"]
    rol = (args.rol or DEFAULT_USER_DATA["rol"]).lower()
    password = args.password or DEFAULT_PASSWORD

    if rol not in role_codes:
        print(f"El rol '{rol}' no es válido. Debe ser uno de: {', '.join(sorted(role_codes))}", file=sys.stderr)
        sys.exit(1)

    missing_fields = [
        field
        for field, value in {
            "email": email,
            "nombre": nombre,
            "cedula": cedula,
            "telefono": telefono,
            "password": password,
            "rol": rol,
        }.items()
        if not value
    ]
    if missing_fields:
        print(
            "Faltan los siguientes campos obligatorios: " + ", ".join(missing_fields),
            file=sys.stderr,
        )
        sys.exit(1)

    if Usuario.objects.filter(email=email).exists():
        print(f"Ya existe un usuario con el email {email}", file=sys.stderr)
        sys.exit(1)

    extra_fields = {
        "nombre": nombre,
        "cedula": cedula,
        "telefono": telefono,
        "rol": rol,
    }

    try:
        user = Usuario.objects.create_user(email=email, password=password, **extra_fields)
    except ValidationError as exc:
        print(f"Error de validación: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Error creando el usuario: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Usuario creado exitosamente: {user.email} ({user.rol})")


if __name__ == "__main__":
    run()

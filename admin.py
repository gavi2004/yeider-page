"""Utility script to create an admin user for the custom Usuario model.

Usage:
    python admin.py run [--email EMAIL --nombre NOMBRE --cedula CEDULA --telefono TELEFONO --password PASSWORD]

Si omites los argumentos, se usarán los valores por defecto definidos en este archivo
para crear el administrador solicitado.
"""

import argparse
import os
import sys

import django
from django.core.exceptions import ValidationError

DEFAULT_ADMIN_DATA = {
    "email": "yeider@gmail.com",
    "nombre": "yeider",
    "cedula": "28591400",
    "telefono": "04262495759",
}

DEFAULT_PASSWORD = os.environ.get("ADMIN_DEFAULT_PASSWORD", "jema2019")


def bootstrap_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proyecto.settings")
    try:
        django.setup()
    except Exception as exc:  # pragma: no cover - defensive
        print(f"No se pudo iniciar Django: {exc}", file=sys.stderr)
        sys.exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Crear un usuario administrador")
    parser.add_argument("command", choices=["run"], help="Acción a realizar")
    parser.add_argument("--email", dest="email", help="Correo del administrador")
    parser.add_argument("--nombre", dest="nombre", help="Nombre completo")
    parser.add_argument("--cedula", dest="cedula", help="Cédula")
    parser.add_argument("--telefono", dest="telefono", help="Teléfono")
    parser.add_argument("--password", dest="password", help="Contraseña del administrador")
    return parser.parse_args()


def run():
    args = parse_arguments()
    if args.command != "run":
        print("Comando no soportado", file=sys.stderr)
        sys.exit(1)

    bootstrap_django()

    from users.models import Usuario

    email = args.email or DEFAULT_ADMIN_DATA["email"]
    nombre = args.nombre or DEFAULT_ADMIN_DATA["nombre"]
    cedula = args.cedula or DEFAULT_ADMIN_DATA["cedula"]
    telefono = args.telefono or DEFAULT_ADMIN_DATA["telefono"]
    password = args.password or DEFAULT_PASSWORD

    missing_fields = [
        field
        for field, value in {
            "email": email,
            "nombre": nombre,
            "cedula": cedula,
            "telefono": telefono,
            "password": password,
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
    }

    try:
        user = Usuario.objects.create_superuser(email=email, password=password, **extra_fields)
    except ValidationError as exc:
        print(f"Error de validación: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Error creando el usuario: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Usuario administrador creado exitosamente: {user.email}")


if __name__ == "__main__":
    run()

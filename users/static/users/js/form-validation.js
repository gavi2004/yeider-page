document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');

    form.addEventListener('submit', function(event) {
        event.preventDefault(); // Prevenir el envío del formulario para validarlo

        let errores = false;
        let errorMessage = '';

        // Validación de la cédula
        const cedula = document.querySelector('[name="cedula"]');
        if (cedula.value.length !== 8 || !/^\d+$/.test(cedula.value)) {
            errores = true;
            errorMessage += 'La cédula debe tener exactamente 8 dígitos numéricos.\n';
        }

        // Validación de teléfono
        const telefono = document.querySelector('[name="telefono"]');
        if (telefono.value.length !== 11 || !/^\d+$/.test(telefono.value)) {
            errores = true;
            errorMessage += 'El teléfono debe contener exactamente 11 dígitos numéricos.\n';
        }

        // Validación de nombre
        const nombre = document.querySelector('[name="nombre"]');
        const nombreRegex = /^[A-Za-záéíóúÁÉÍÓÚ\s]+$/; // Solo letras y espacios
        if (!nombreRegex.test(nombre.value)) {
            errores = true;
            errorMessage += 'El nombre solo puede contener letras, no debe contener números ni ningún caracter especial.\n';
        }

        // Validación de email
        const email = document.querySelector('[name="email"]');
        const emailRegex = /^[a-zA-Z0-9._%+-]+@(gmail\.com|proton\.me|outlook\.com)$/;
        if (!emailRegex.test(email.value)) {
            errores = true;
            errorMessage += 'El correo debe ser de tipo Gmail, Proton o Outlook.\n';
        }

        // Validación de contraseñas
        const password = document.querySelector('[name="password"]');
        const confirmarPassword = document.querySelector('[name="confirmar_password"]');

        if (password.value !== confirmarPassword.value) {
            errores = true;
            errorMessage += 'Las contraseñas no coinciden.\n';
        }

        if (password.value.length < 8) {
            errores = true;
            errorMessage += 'La contraseña debe tener al menos 8 caracteres.\n';
        }

        const mayusculaRegex = /[A-Z]/;
        if (!mayusculaRegex.test(password.value)) {
            errores = true;
            errorMessage += 'La contraseña debe contener al menos una letra mayúscula.\n';
        }

        const caracterEspecialRegex = /[!@#$%^&*(),.?":{}|<>]/;
        if (!caracterEspecialRegex.test(password.value)) {
            errores = true;
            errorMessage += 'La contraseña debe contener al menos un carácter especial (como !, @, #, etc).\n';
        }

        // Si hay errores, mostrar un SweetAlert con el mensaje
        if (errores) {
            Swal.fire({
                icon: 'error',
                title: '¡Error!',
                text: errorMessage
            });
        } else {
            // Si no hay errores, hacer la verificación en el backend para comprobar si ya existen los datos
            const cedulaValue = cedula.value;
            const telefonoValue = telefono.value;
            const emailValue = email.value;

            fetch('/verificar-datos/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name="csrfmiddlewaretoken"]').value
                },
                body: JSON.stringify({
                    cedula: cedulaValue,
                    telefono: telefonoValue,
                    email: emailValue
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.existe) {
                    // Mostrar mensaje de error si los datos ya existen
                    Swal.fire({
                        icon: 'error',
                        title: '¡Error!',
                        text: 'El usuario con esa cédula, teléfono o email ya está registrado.'
                    });
                } else {
                    // Si no existen los datos, se puede enviar el formulario
                    Swal.fire({
                        icon: 'success',
                        title: '¡Registro Exitoso!',
                        text: '¡Te has registrado exitosamente!',
                        showConfirmButton: false,
                        timer: 2000
                    }).then(() => {
                        form.submit(); // Enviar el formulario al servidor
                    });
                }
            })
            .catch(error => {
                console.error('Error al verificar los datos:', error);
                Swal.fire({
                    icon: 'error',
                    title: '¡Error!',
                    text: 'Ocurrió un problema al verificar los datos. Inténtalo de nuevo.'
                });
            });
        }
    });
});

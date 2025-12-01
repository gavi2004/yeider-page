document.addEventListener('DOMContentLoaded', function () {
    const campos = ['cedula', 'email', 'telefono', 'nombre', 'password', 'confirmar_password'];
    const errores = {};

    // Validar campo en tiempo real
    async function validarCampo(nombreCampo, inputElement) {
        const valor = inputElement.value;

        if (valor.length > 3) {
            const res = await fetch(`/validar_dato/?campo=${nombreCampo}&valor=${valor}`);
            const data = await res.json();
            let errorSpan = document.querySelector(`#error_${nombreCampo}`);

            if (!errorSpan) {
                errorSpan = document.createElement("span");
                errorSpan.id = `error_${nombreCampo}`;
                errorSpan.style.color = "red";
                inputElement.parentNode.appendChild(errorSpan);
            }

            if (data.existe) {
                errorSpan.textContent = `Este ${nombreCampo} ya está registrado.`;
                errores[nombreCampo] = true;
            } else {
                errorSpan.textContent = "";
                delete errores[nombreCampo];
            }
        }
    }

    campos.forEach(campo => {
        const input = document.querySelector(`[name="${campo}"]`);
        if (input) {
            input.addEventListener('input', () => validarCampo(campo, input));
        }
    });

    // Mostrar errores del backend si existen
    if (typeof window.formErrors !== 'undefined' && Object.keys(window.formErrors).length > 0) {
        let mensaje = "";
        for (const [campo, lista] of Object.entries(window.formErrors)) {
            let errorSpan = document.querySelector(`#error_${campo}`);
            if (!errorSpan) {
                errorSpan = document.createElement("span");
                errorSpan.id = `error_${campo}`;
                errorSpan.style.color = "red";
                document.querySelector(`[name="${campo}"]`).parentNode.appendChild(errorSpan);
            }
            errorSpan.textContent = lista.join(', ');
        }

        Swal.fire({
            icon: 'error',
            title: 'Errores en el formulario',
            text: 'Revisa los campos con errores marcados en rojo.'
        });
    }

    // Validar formulario antes de enviar
    const formulario = document.querySelector("#form-usuario");

    formulario.addEventListener("submit", async function (e) {
        e.preventDefault();  // Evita el submit clásico

        // Evitar enviar si hay errores locales
        if (Object.keys(errores).length > 0) {
            Swal.fire({
                icon: 'error',
                title: 'Hay errores en el formulario',
                text: 'Por favor, corrija los errores antes de enviar.'
            });
            return;
        }

        const formData = new FormData(formulario);
        const res = await fetch('/validar_y_registrar/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const data = await res.json();

        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Registro exitoso',
                text: 'El usuario fue registrado correctamente.'
            });
            formulario.reset();
        } else {
            // Mostrar errores del backend
            for (const [campo, mensajes] of Object.entries(data.errors)) {
                let errorSpan = document.querySelector(`#error_${campo}`);
                const inputElement = document.querySelector(`[name="${campo}"]`);

                if (!errorSpan) {
                    errorSpan = document.createElement("span");
                    errorSpan.id = `error_${campo}`;
                    errorSpan.style.color = "red";
                    inputElement.parentNode.appendChild(errorSpan);
                }

                errorSpan.textContent = mensajes.join(', ');
            }

            Swal.fire({
                icon: 'error',
                title: 'Errores en el formulario',
                text: 'Revisa los campos con errores.'
            });
        }
    });
});

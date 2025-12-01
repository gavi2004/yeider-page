document.addEventListener('DOMContentLoaded', function () {
    const erroresElement = document.getElementById('errores-json');

    if (erroresElement) {
        const errores = JSON.parse(erroresElement.textContent);

        if (errores.length > 0) {
            Swal.fire({
                icon: 'error',
                title: 'Errores en el formulario',
                html: '<ul style="text-align:left;">' + errores.map(e => `<li>${e}</li>`).join('') + '</ul>',
                confirmButtonText: 'Aceptar'
            });
        }
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const deleteForms = document.querySelectorAll('.delete-form');

    deleteForms.forEach(function(form) {
        form.addEventListener('submit', function (e) {
            const userName = form.getAttribute('data-username');
            const confirmacion = confirm(`¿Estás seguro que deseas eliminar al usuario ${userName}? Esta acción no se puede deshacer.`);
            if (!confirmacion) {
                e.preventDefault();
            }
        });
    });
});

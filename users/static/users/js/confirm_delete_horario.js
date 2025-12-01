function confirmarEliminacion(formElement) {
    const nombreHorario = formElement.querySelector('button').dataset.horarioNombre;
    return confirm(`¿Estás seguro de que deseas eliminar el horario "${nombreHorario}"? Esta acción no se puede deshacer.`);
}
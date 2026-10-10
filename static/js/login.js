/* Pantalla de ingreso */
document.getElementById('formLogin').addEventListener('submit', async function(e) {
    e.preventDefault();
    const err = document.getElementById('errorLogin');
    err.classList.add('d-none');
    try {
        const data = await API.login(
            document.getElementById('usuario').value,
            document.getElementById('password').value
        );
        API.guardarSesion(data);
        window.location.replace('/panel/');
    } catch (ex) {
        Aviso.mostrar(ex.message || 'Error de acceso.');
    }
});
function exigirLogin() {
    if (API.token()) {
        window.location.replace('/panel/');
    }
}
exigirLogin();
window.addEventListener('pageshow', function() {
    exigirLogin();
});
window.addEventListener('popstate', function() {
    if (!API.token()) {
        history.pushState(null, '', location.href);
    }
});
history.pushState(null, '', location.href);

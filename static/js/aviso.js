/* Ventanas emergentes — solo botones para cerrar o confirmar */
const Aviso = {
    _iniciado: false,
    _resolverConfirm: null,
    _resolverPassword: null,

    iniciar() {
        if (this._iniciado) return;
        if (!document.getElementById('modalAviso')) return;
        document.getElementById('btnModalAvisoCerrar').onclick = () => this.cerrar();
        document.getElementById('btnModalConfirmarSi').onclick = () => this._cerrarConfirm(true);
        document.getElementById('btnModalConfirmarNo').onclick = () => this._cerrarConfirm(false);
        document.getElementById('btnModalPasswordSi').onclick = () => this._cerrarPassword(true);
        document.getElementById('btnModalPasswordNo').onclick = () => this._cerrarPassword(false);
        const inpPwd = document.getElementById('modalPasswordInput');
        if (inpPwd) {
            inpPwd.onkeydown = (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this._cerrarPassword(true);
                }
            };
        }
        this._iniciado = true;
    },

    limpiarTexto(mensaje) {
        let t = String(mensaje || '').trim();
        t = t.replace(/https?:\/\/[^\s]*/gi, '');
        t = t.replace(/localhost[^\s]*/gi, '');
        t = t.replace(/127\.0\.0\.1[^\s]*/gi, '');
        t = t.replace(/\s+/g, ' ').trim();
        if (!t) return 'Operación no completada.';
        if (t.toLowerCase().startsWith('aviso:')) {
            return t.replace(/^aviso:\s*/i, '').trim() || 'Operación no completada.';
        }
        return t;
    },

    mostrar(mensaje) {
        this.iniciar();
        document.getElementById('modalAvisoMensaje').textContent = this.limpiarTexto(mensaje);
        document.getElementById('modalAviso').classList.remove('oculto');
    },

    confirmar(mensaje) {
        this.iniciar();
        const self = this;
        return new Promise(function(resolve) {
            self._resolverConfirm = resolve;
            document.getElementById('modalConfirmarMensaje').textContent = self.limpiarTexto(mensaje);
            document.getElementById('modalConfirmar').classList.remove('oculto');
        });
    },

    pedirContrasena(mensaje) {
        this.iniciar();
        const self = this;
        const inp = document.getElementById('modalPasswordInput');
        inp.value = '';
        document.getElementById('modalPasswordMensaje').textContent = self.limpiarTexto(mensaje);
        document.getElementById('modalPassword').classList.remove('oculto');
        inp.focus();
        return new Promise(function(resolve) {
            self._resolverPassword = resolve;
        });
    },

    _cerrarConfirm(resultado) {
        document.getElementById('modalConfirmar').classList.add('oculto');
        if (this._resolverConfirm) {
            this._resolverConfirm(resultado);
            this._resolverConfirm = null;
        }
    },

    _cerrarPassword(aceptar) {
        const modal = document.getElementById('modalPassword');
        const inp = document.getElementById('modalPasswordInput');
        const valor = aceptar ? inp.value : null;
        modal.classList.add('oculto');
        inp.value = '';
        if (this._resolverPassword) {
            this._resolverPassword(valor);
            this._resolverPassword = null;
        }
    },

    pacienteNoExiste() {
        this.mostrar('No existe ningún paciente registrado con esos datos.');
    },

    cerrar() {
        const m = document.getElementById('modalAviso');
        if (m) m.classList.add('oculto');
    },
};

document.addEventListener('DOMContentLoaded', () => Aviso.iniciar());

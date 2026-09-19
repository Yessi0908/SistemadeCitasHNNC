/* Ventanas emergentes — solo botones para cerrar o confirmar */
const Aviso = {
    _iniciado: false,
    _resolverConfirm: null,
    _resolverPassword: null,
    _pideMotivo: false,

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
        const inpMotivo = document.getElementById('modalConfirmarMotivo');
        if (inpMotivo) {
            inpMotivo.oninput = () => this._actualizarBotonMotivo();
        }
        this._iniciado = true;
    },

    limpiarTexto(mensaje) {
        let t = String(mensaje || '').trim();
        t = t.replace(/https?:\/\/[^\s]*/gi, '');
        t = t.replace(/localhost[^\s]*/gi, '');
        t = t.replace(/127\.0\.0\.1[^\s]*/gi, '');
        t = t.replace(/[ \t]+/g, ' ').trim();
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
            self._pideMotivo = false;
            self._prepararConfirmacion(mensaje, false);
        });
    },

    pedirJustificacion(mensaje, textoBoton) {
        this.iniciar();
        const self = this;
        return new Promise(function(resolve) {
            self._resolverConfirm = resolve;
            self._pideMotivo = true;
            self._textoBotonMotivo = textoBoton || 'Confirmar';
            self._prepararConfirmacion(mensaje, true);
        });
    },

    _prepararConfirmacion(mensaje, conMotivo) {
        document.getElementById('modalConfirmarMensaje').textContent = this.limpiarTexto(mensaje);
        const caja = document.getElementById('modalConfirmarMotivoCaja');
        const inp = document.getElementById('modalConfirmarMotivo');
        const btnSi = document.getElementById('btnModalConfirmarSi');
        if (caja && inp) {
            if (conMotivo) {
                caja.classList.remove('oculto');
                inp.value = '';
                btnSi.textContent = this._textoBotonMotivo || 'Confirmar';
                btnSi.disabled = true;
                setTimeout(function() { inp.focus(); }, 50);
            } else {
                caja.classList.add('oculto');
                inp.value = '';
                btnSi.textContent = 'Confirmar';
                btnSi.disabled = false;
            }
        }
        document.getElementById('modalConfirmar').classList.remove('oculto');
    },

    _actualizarBotonMotivo() {
        if (!this._pideMotivo) return;
        const inp = document.getElementById('modalConfirmarMotivo');
        const btnSi = document.getElementById('btnModalConfirmarSi');
        if (!inp || !btnSi) return;
        btnSi.disabled = String(inp.value || '').trim().length < 8;
    },

    _cerrarConfirm(resultado) {
        const inp = document.getElementById('modalConfirmarMotivo');
        const motivo = inp ? String(inp.value || '').trim() : '';
        document.getElementById('modalConfirmar').classList.add('oculto');
        const pideMotivo = this._pideMotivo;
        this._pideMotivo = false;
        if (inp) inp.value = '';
        const caja = document.getElementById('modalConfirmarMotivoCaja');
        if (caja) caja.classList.add('oculto');
        const btnSi = document.getElementById('btnModalConfirmarSi');
        if (btnSi) {
            btnSi.disabled = false;
            btnSi.textContent = 'Confirmar';
        }
        if (!this._resolverConfirm) return;
        const resolver = this._resolverConfirm;
        this._resolverConfirm = null;
        if (pideMotivo) {
            resolver(resultado ? motivo : null);
        } else {
            resolver(resultado);
        }
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

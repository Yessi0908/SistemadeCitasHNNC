/* Cliente API — JWT */
const API = {
    base: '/api',

    token() { return sessionStorage.getItem('access'); },
    refresh() { return sessionStorage.getItem('refresh'); },
    rol() { return sessionStorage.getItem('rol'); },

    guardarSesion(data) {
        sessionStorage.setItem('access', data.access);
        sessionStorage.setItem('refresh', data.refresh);
        sessionStorage.setItem('rol', data.rol);
        sessionStorage.setItem('username', data.username);
        sessionStorage.setItem('nombre', data.nombre || data.username);
        if (data.user_id != null) sessionStorage.setItem('user_id', String(data.user_id));
    },

    limpiarSesion() {
        ['access', 'refresh', 'rol', 'username', 'nombre', 'user_id'].forEach(k => sessionStorage.removeItem(k));
    },

    async login(usuario, password) {
        const res = await fetch(this.base + '/auth/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: usuario, password: password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error de login');
        return data;
    },

    async logout() {
        const refresh = this.refresh();
        try {
            await fetch(this.base + '/auth/logout/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + this.token(),
                },
                body: JSON.stringify({ refresh: refresh }),
            });
        } catch (e) { /* ignorar */ }
        this.limpiarSesion();
    },

    async peticion(url, opciones = {}) {
        const headers = Object.assign(
            { 'Content-Type': 'application/json' },
            opciones.headers || {}
        );
        if (this.token()) headers['Authorization'] = 'Bearer ' + this.token();

        let res = await fetch(this.base + url, Object.assign({}, opciones, { headers }));

        if (res.status === 401 && this.refresh()) {
            const ok = await this.refrescarToken();
            if (ok) {
                headers['Authorization'] = 'Bearer ' + this.token();
                res = await fetch(this.base + url, Object.assign({}, opciones, { headers }));
            }
        }

        if (res.status === 401) {
            this.limpiarSesion();
            window.location.href = '/login/';
            throw new Error('Sesión expirada');
        }
        return res;
    },

    async refrescarToken() {
        try {
            const res = await fetch(this.base + '/auth/token/refresh/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh: this.refresh() }),
            });
            if (!res.ok) return false;
            const data = await res.json();
            sessionStorage.setItem('access', data.access);
            return true;
        } catch (e) { return false; }
    },

    async get(url) {
        const res = await this.peticion(url);
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(this._mensajeError(err) || err.error || 'Error en consulta');
        }
        return res.json();
    },

    async post(url, body) {
        const res = await this.peticion(url, { method: 'POST', body: JSON.stringify(body) });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(API._mensajeError(err) || 'Error');
        }
        return res.json();
    },

    _mensajeError(err) {
        if (!err || typeof err !== 'object') return '';
        let texto = '';
        if (typeof err.detail === 'string') texto = err.detail;
        else {
            const partes = [];
            Object.keys(err).forEach(function(k) {
                const v = err[k];
                partes.push(Array.isArray(v) ? v.join(' ') : String(v));
            });
            texto = partes.join(' — ');
        }
        return texto.replace(/https?:\/\/[^\s]*/gi, '').replace(/localhost[^\s]*/gi, '').trim();
    },

    async put(url, body) {
        const res = await this.peticion(url, { method: 'PUT', body: JSON.stringify(body) });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(this._mensajeError(err) || err.error || 'Error al actualizar');
        }
        return res.json();
    },

    async patch(url, body) {
        const res = await this.peticion(url, { method: 'PATCH', body: JSON.stringify(body) });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(API._mensajeError(err) || 'Error al actualizar');
        }
        return res.json();
    },

    async delete(url) {
        const res = await this.peticion(url, { method: 'DELETE' });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(API._mensajeError(err) || 'Error al eliminar');
        }
        if (res.status === 204) return {};
        return res.json().catch(() => ({}));
    },

    descargarPdfPut(url) {
        fetch(this.base + url, {
            method: 'PUT',
            headers: { 'Authorization': 'Bearer ' + this.token() },
        }).then(async function(r) {
            if (!r.ok) {
                const err = await r.json().catch(function() { return {}; });
                throw new Error(API._mensajeError(err) || err.error || 'No se pudo generar el PDF');
            }
            return r.blob();
        }).then(function(blob) {
            const u = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = u;
            a.download = 'registro_diario.pdf';
            a.click();
            URL.revokeObjectURL(u);
        }).catch(function(e) { Aviso.mostrar(e.message); });
    },

    descargarPdf(url) {
        const a = document.createElement('a');
        a.href = this.base + url + (url.includes('?') ? '&' : '?') + 't=' + Date.now();
        // Usar fetch con token para PDF autenticado
        fetch(this.base + url, { headers: { 'Authorization': 'Bearer ' + this.token() } })
            .then(r => r.blob())
            .then(blob => {
                const u = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = u;
                link.download = 'documento.pdf';
                link.click();
                URL.revokeObjectURL(u);
            });
    },
};

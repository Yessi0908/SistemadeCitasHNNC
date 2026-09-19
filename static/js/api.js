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
            window.location.replace('/login/');
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

    async delete(url, body) {
        const opciones = { method: 'DELETE' };
        if (body) opciones.body = JSON.stringify(body);
        const res = await this.peticion(url, opciones);
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(API._mensajeError(err) || 'Error al eliminar');
        }
        if (res.status === 204) return {};
        return res.json().catch(() => ({}));
    },

    _nombreDescarga(res, fallback) {
        const cd = res.headers.get('Content-Disposition') || '';
        const utf8 = /filename\*=UTF-8''([^;]+)/i.exec(cd);
        if (utf8) {
            try { return decodeURIComponent(utf8[1]); } catch (e) { /* usar otro */ }
        }
        const quoted = /filename="([^"]+)"/i.exec(cd);
        if (quoted) return quoted[1];
        const plain = /filename=([^;]+)/i.exec(cd);
        if (plain) return plain[1].trim();
        return fallback;
    },

    _guardarBlob(blob, nombre) {
        const u = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = u;
        a.download = nombre;
        a.click();
        URL.revokeObjectURL(u);
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
            const nombre = API._nombreDescarga(r, 'registro_diario.pdf');
            const blob = await r.blob();
            API._guardarBlob(blob, nombre);
        }).catch(function(e) { Aviso.mostrar(e.message); });
    },

    descargarPdf(url) {
        fetch(this.base + url, { headers: { 'Authorization': 'Bearer ' + this.token() } })
            .then(async function(r) {
                if (!r.ok) {
                    const err = await r.json().catch(function() { return {}; });
                    throw new Error(API._mensajeError(err) || err.error || 'No se pudo generar el PDF');
                }
                const nombre = API._nombreDescarga(r, 'documento.pdf');
                const blob = await r.blob();
                API._guardarBlob(blob, nombre);
            })
            .catch(function(e) { Aviso.mostrar(e.message); });
    },
};

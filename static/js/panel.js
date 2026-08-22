/* Panel principal — módulos por rol */
(function() {
    if (!API.token()) { window.location.href = '/login/'; return; }

    const rol = API.rol();
    document.getElementById('usuarioActivo').textContent = sessionStorage.getItem('nombre');
    document.getElementById('rolActivo').textContent = rol.toUpperCase();

    // Menús según rol — cada rol solo ve lo suyo
    const MENUS = {
        archivo: [
            { id: 'sec-archivo-buscar', texto: 'Buscar expedientes' },
            { id: 'sec-archivo-citas', texto: 'Buscar citas' },
            { id: 'sec-archivo-registro', texto: 'Hoja de registro' },
        ],
        registros: [
            { id: 'sec-registros-pacientes', texto: 'Pacientes' },
            { id: 'sec-registros-citas', texto: 'Citas médicas' },
            { id: 'sec-registros-diario', texto: 'Registro diario' },
        ],
        estadistica: [
            { id: 'sec-estadistica', texto: 'Estadísticas (tablas)' },
        ],
        juridico: [
            { id: 'sec-juridico-vas', texto: 'Módulo VAS' },
        ],
        admin: [
            { id: 'sec-registros-pacientes', texto: 'Pacientes' },
            { id: 'sec-registros-citas', texto: 'Citas' },
            { id: 'sec-registros-diario', texto: 'Registro diario' },
            { id: 'sec-estadistica', texto: 'Estadísticas' },
            { id: 'sec-juridico-vas', texto: 'VAS' },
            { id: 'sec-archivo-buscar', texto: 'Consulta archivo' },
            { id: 'sec-archivo-citas', texto: 'Citas (archivo)' },
            { id: 'sec-archivo-registro', texto: 'Hoja registro' },
            { id: 'sec-admin-medicos', texto: 'Médicos' },
            { id: 'sec-admin-usuarios', texto: 'Usuarios' },
            { id: 'sec-admin-bitacora', texto: 'Bitácora' },
            { id: 'sec-admin-config', texto: 'Configuración' },
            { id: 'sec-admin-bd', texto: 'Ver base de datos' },
            { id: 'sec-admin-api', texto: 'Documentación API' },
        ],
    };

    const menu = document.getElementById('menuLateral');
    (MENUS[rol] || []).forEach((item, i) => {
        const btn = document.createElement('button');
        btn.textContent = item.texto;
        btn.dataset.seccion = item.id;
        if (i === 0) btn.classList.add('activo');
        btn.onclick = () => mostrarSeccion(item.id, btn);
        menu.appendChild(btn);
    });

    function mostrarSeccion(id, btn) {
        document.querySelectorAll('[id^="sec-"]').forEach(s => {
            s.classList.remove('seccion-activa');
            s.classList.add('seccion-oculta');
        });
        document.getElementById('seccionInicio').classList.add('seccion-oculta');
        document.getElementById('seccionInicio').classList.remove('seccion-activa');
        const sec = document.getElementById(id);
        if (sec) {
            sec.classList.remove('seccion-oculta');
            sec.classList.add('seccion-activa');
        }
        menu.querySelectorAll('button').forEach(b => b.classList.remove('activo'));
        if (btn) btn.classList.add('activo');
        cargarSeccion(id);
    }

    if (MENUS[rol] && MENUS[rol][0]) {
        mostrarSeccion(MENUS[rol][0].id, menu.querySelector('button'));
    }

    document.getElementById('btnSalir').onclick = async () => {
        await API.logout();
        window.location.href = '/login/';
    };

    // Atajos F5 F6 F7
    document.addEventListener('keydown', function(e) {
        const id = document.getElementById('pacienteSeleccionadoId').value;
        if (!id) return;
        if (e.key === 'F5') { e.preventDefault(); API.descargarPdf('/pacientes/' + id + '/constancia/'); }
        if (e.key === 'F6') { e.preventDefault(); API.descargarPdf('/pacientes/' + id + '/hoja_expediente/'); }
        if (e.key === 'F7') { e.preventDefault(); API.descargarPdf('/pacientes/' + id + '/carnet/'); }
    });

    function cargarSeccion(id) {
        if (id === 'sec-archivo-buscar') return;
        if (id === 'sec-archivo-citas') initArchivoCitas();
        if (id === 'sec-archivo-registro') initArchivoRegistro();
        if (id === 'sec-registros-pacientes') cargarPacientes();
        if (id === 'sec-registros-citas') cargarCitas();
        if (id === 'sec-registros-diario') cargarDiario();
        if (id === 'sec-estadistica') cargarEstadistica();
        if (id === 'sec-juridico-vas') cargarVAS();
        if (id === 'sec-admin-medicos') cargarMedicosAdmin();
        if (id === 'sec-admin-usuarios') cargarUsuarios();
        if (id === 'sec-admin-bitacora') cargarBitacora();
        if (id === 'sec-admin-bd') initVerBaseDatos();
        if (id === 'sec-admin-api') { /* enlace externo */ }
    }

    function hoyISO() {
        return new Date().toISOString().slice(0, 10);
    }

    function aplicarLimitesFechas() {
        const hoy = hoyISO();
        const maxPasado = ['pac_fecha_nacimiento', 'pac_fecha_ingreso', 'fechaDiario', 'archivoRegistroFecha'];
        maxPasado.forEach(function(id) {
            const el = document.getElementById(id);
            if (el) el.max = hoy;
        });
        const minFuturo = ['citaFecha'];
        minFuturo.forEach(function(id) {
            const el = document.getElementById(id);
            if (el) el.min = hoy;
        });
    }

    // --- ARCHIVO ---
    document.getElementById('btnArchivoBuscar').onclick = async () => {
        const q = document.getElementById('archivoQ').value.trim();
        if (!q) { Aviso.mostrar('Escriba nombre, DPI o número de expediente.'); return; }
        const data = await API.get('/archivo/buscar/?q=' + encodeURIComponent(q));
        const div = document.getElementById('archivoResultados');
        renderPacientesTabla(div, Array.isArray(data) ? data : [], true, true);
    };

    async function llenarEspecialidadesArchivo() {
        const sel = document.getElementById('archivoCitaEspecialidad');
        if (!sel || sel.options.length > 1) return;
        try {
            const cat = await API.get('/catalogos/paciente/');
            (cat.especialidades || []).forEach(function(e) {
                const o = document.createElement('option');
                o.value = e;
                o.textContent = e;
                sel.appendChild(o);
            });
        } catch (e) { /* ignorar */ }
    }

    function initArchivoCitas() {
        llenarEspecialidadesArchivo();
    }

    const btnArchivoCitas = document.getElementById('btnArchivoBuscarCitas');
    if (btnArchivoCitas) {
        btnArchivoCitas.onclick = async function() {
            const fecha = document.getElementById('archivoCitaFecha').value;
            const esp = document.getElementById('archivoCitaEspecialidad').value;
            if (!fecha && !esp) {
                Aviso.mostrar('Indique al menos fecha o especialidad.');
                return;
            }
            let url = '/archivo/citas/?';
            if (fecha) url += 'fecha=' + fecha + '&';
            if (esp) url += 'especialidad=' + encodeURIComponent(esp);
            const data = await API.get(url);
            const div = document.getElementById('archivoCitasResultados');
            const lista = Array.isArray(data) ? data : [];
            if (!lista.length) {
                div.innerHTML = '';
                Aviso.mostrar('No hay citas con los filtros indicados.');
                return;
            }
            let html = '<table class="tabla-sistema"><thead><tr><th>Fecha</th><th>Hora</th><th>Expediente</th><th>Paciente</th><th>Especialidad</th><th>Médico</th><th>Estado</th></tr></thead><tbody>';
            lista.forEach(function(c) {
                html += '<tr><td>' + c.fecha + '</td><td>' + (c.hora || '').slice(0, 5) + '</td><td>' + (c.numero_expediente || '') + '</td><td>' + (c.paciente_nombre || '') + '</td><td>' + c.especialidad + '</td><td>' + (c.medico_nombre || '—') + '</td><td>' + c.estado + '</td></tr>';
            });
            html += '</tbody></table><p class="texto-ayuda mt-2">Total: ' + lista.length + ' cita(s)</p>';
            div.innerHTML = html;
        };
    }

    function initArchivoRegistro() {
        const inp = document.getElementById('archivoRegistroFecha');
        if (inp && !inp.value) inp.value = hoyISO();
        aplicarLimitesFechas();
    }

    const btnArchivoReg = document.getElementById('btnArchivoImprimirRegistro');
    if (btnArchivoReg) {
        btnArchivoReg.onclick = function() {
            const f = document.getElementById('archivoRegistroFecha').value;
            if (!f) { Aviso.mostrar('Seleccione la fecha.'); return; }
            if (f > hoyISO()) { Aviso.mostrar('La fecha del registro no puede ser futura.'); return; }
            API.descargarPdfPut('/registro-diario/?fecha=' + f);
        };
    }

    const btnArchivoRegVer = document.getElementById('archivoRegistroFecha');
    if (btnArchivoRegVer) {
        btnArchivoRegVer.addEventListener('change', async function() {
            const f = this.value;
            if (!f) return;
            try {
                const data = await API.get('/registro-diario/?fecha=' + f);
                let html = '<p>Total pacientes: ' + (data.registro?.total_pacientes || 0) + '</p>';
                html += '<table class="tabla-sistema"><thead><tr><th>#</th><th>Expediente</th><th>Paciente</th><th>Especialidad</th></tr></thead><tbody>';
                (data.detalles || []).forEach(function(d) {
                    html += '<tr><td>' + d.orden + '</td><td>' + d.expediente + '</td><td>' + d.paciente_nombre + '</td><td>' + (d.especialidad || '') + '</td></tr>';
                });
                html += '</tbody></table>';
                document.getElementById('archivoRegistroVista').innerHTML = html || '<p>Sin pacientes en este día</p>';
            } catch (e) {
                document.getElementById('archivoRegistroVista').innerHTML = '<p>Sin registro para esta fecha</p>';
            }
        });
    }

    // --- PACIENTES ---
    let CATALOGOS = {
        especialidades: [],
        especialidades_tarde: ['Psicología Tarde (PST)', 'Medicina General Tarde (MGT)'],
        estados_paciente: ['Control', 'Primera vez'],
        estados_civiles: ['Soltero(a)', 'Casado(a)', 'Viudo(a)'],
        estados_cita: ['Confirmada', 'Cancelada', 'Atendida'],
        medicos: [],
    };
    let MEDICOS = [];

    const CAMPOS_PACIENTE = [
        ['primer_apellido', 'Primer apellido'],
        ['segundo_apellido', 'Segundo apellido'],
        ['primer_nombre', 'Primer nombre'],
        ['segundo_nombre', 'Segundo nombre'],
        ['dpi', 'DPI'],
        ['direccion', 'Dirección'],
        ['telefono', 'Teléfono'],
        ['contacto_emergencia_nombre', 'Contacto de emergencia (nombre)'],
        ['contacto_emergencia_telefono', 'Contacto de emergencia (teléfono)'],
        ['lugar_nacimiento', 'Lugar de nacimiento'],
        ['fecha_nacimiento', 'Fecha de nacimiento', 'date'],
        ['sexo', 'Sexo', 'sexo'],
        ['estado_civil', 'Estado civil', 'estado_civil'],
        ['ocupacion', 'Ocupación'],
        ['nacionalidad', 'Nacionalidad'],
        ['nombre_conyuge', 'Nombre del cónyuge'],
        ['nombre_padre', 'Nombre del padre'],
        ['nombre_madre', 'Nombre de la madre'],
        ['fecha_ingreso', 'Fecha de ingreso', 'date'],
        ['especialidad', 'Especialidad', 'especialidad'],
        ['estado_paciente', 'Estado', 'estado_paciente'],
    ];

    function calcularEdadDesdeFecha(fechaStr) {
        if (!fechaStr) return null;
        const partes = fechaStr.split('-');
        const n = new Date(parseInt(partes[0], 10), parseInt(partes[1], 10) - 1, parseInt(partes[2], 10));
        const h = new Date();
        let anios = h.getFullYear() - n.getFullYear();
        let meses = h.getMonth() - n.getMonth();
        let dias = h.getDate() - n.getDate();
        if (dias < 0) {
            meses -= 1;
            dias += new Date(h.getFullYear(), h.getMonth(), 0).getDate();
        }
        if (meses < 0) {
            anios -= 1;
            meses += 12;
        }
        return { anios: Math.max(anios, 0), meses: Math.max(meses, 0), dias: Math.max(dias, 0) };
    }

    function textoEdadPartes(anios, meses, dias) {
        return anios + ' años, ' + meses + ' meses, ' + dias + ' días';
    }

    function textoEdadPaciente(p) {
        if (!p) return '—';
        if (p.edad_texto && p.edad_texto !== '—') return p.edad_texto;
        if (p.fecha_nacimiento) {
            const e = calcularEdadDesdeFecha(p.fecha_nacimiento);
            return e ? textoEdadPartes(e.anios, e.meses, e.dias) : '—';
        }
        if (p.edad_anios || p.edad_meses || p.edad_dias) {
            return textoEdadPartes(p.edad_anios || 0, p.edad_meses || 0, p.edad_dias || 0);
        }
        return '—';
    }

    function actualizarEdadEnFormulario() {
        const bloque = document.getElementById('bloqueEdadPaciente');
        const valor = document.getElementById('edadPacienteValor');
        const inp = document.getElementById('pac_fecha_nacimiento');
        if (!bloque || !valor) return;
        if (!inp || !inp.value) {
            bloque.classList.add('oculto');
            valor.textContent = '—';
            return;
        }
        const e = calcularEdadDesdeFecha(inp.value);
        bloque.classList.remove('oculto');
        valor.textContent = e ? textoEdadPartes(e.anios, e.meses, e.dias) : '—';
    }

    function crearSelectOpciones(opciones, valorDefecto) {
        const sel = document.createElement('select');
        sel.innerHTML = '<option value="">-- Seleccionar --</option>';
        opciones.forEach(function(opt) {
            const o = document.createElement('option');
            o.value = opt;
            o.textContent = opt;
            if (valorDefecto && valorDefecto === opt) o.selected = true;
            sel.appendChild(o);
        });
        return sel;
    }

    function construirFormulario() {
        const form = document.getElementById('formPaciente');
        form.innerHTML = '';
        CAMPOS_PACIENTE.forEach(function(c) {
            const wrap = document.createElement('div');
            const lbl = document.createElement('label');
            lbl.textContent = c[1];
            let inp;
            if (c[2] === 'date') {
                inp = document.createElement('input');
                inp.type = 'date';
                if (c[0] === 'fecha_nacimiento') {
                    inp.addEventListener('change', actualizarEdadEnFormulario);
                    inp.addEventListener('input', actualizarEdadEnFormulario);
                }
            } else if (c[2] === 'sexo') {
                inp = document.createElement('select');
                inp.innerHTML = '<option value="">-- Seleccionar --</option><option value="M">Masculino</option><option value="F">Femenino</option>';
            } else if (c[2] === 'estado_civil') {
                inp = crearSelectOpciones(CATALOGOS.estados_civiles);
            } else if (c[2] === 'especialidad') {
                inp = crearSelectOpciones(CATALOGOS.especialidades);
            } else if (c[2] === 'estado_paciente') {
                inp = crearSelectOpciones(CATALOGOS.estados_paciente);
            } else {
                inp = document.createElement('input');
                inp.type = 'text';
            }
            inp.name = c[0];
            inp.id = 'pac_' + c[0];
            wrap.appendChild(lbl);
            wrap.appendChild(inp);
            form.appendChild(wrap);
        });
        const bloqueEdad = document.createElement('div');
        bloqueEdad.id = 'bloqueEdadPaciente';
        bloqueEdad.className = 'bloque-edad-auto oculto';
        bloqueEdad.innerHTML = '<label>Edad calculada automáticamente</label><p class="edad-valor mb-0" id="edadPacienteValor">—</p>';
        form.appendChild(bloqueEdad);
        aplicarLimitesFechas();
    }

    async function cargarCatalogos() {
        try {
            CATALOGOS = await API.get('/catalogos/paciente/');
            MEDICOS = CATALOGOS.medicos || [];
        } catch (e) { /* usar valores por defecto */ }
    }

    async function initFormularioPaciente() {
        await cargarCatalogos();
        construirFormulario();
        llenarSelectEspecialidadesCita();
        llenarSelectEspecialidadesMedicoAdmin();
    }
    initFormularioPaciente();

    let pacienteEditId = null;
    let pacienteCitasActivoId = null;

    function tablaCitasHtml(lista, textoVacio) {
        if (!lista || !lista.length) {
            return '<p class="texto-ayuda">' + textoVacio + '</p>';
        }
        let html = '<table class="tabla-sistema"><thead><tr><th>Fecha</th><th>Hora</th><th>Especialidad</th><th>Médico</th><th>Estado</th></tr></thead><tbody>';
        lista.forEach(function(c) {
            html += '<tr><td>' + c.fecha + '</td><td>' + (c.hora || '').slice(0, 5) + '</td><td>' + c.especialidad + '</td><td>' + (c.medico_nombre || '—') + '</td><td>' + (c.estado || '') + '</td></tr>';
        });
        return html + '</tbody></table>';
    }

    function renderPanelCitas(panel, data) {
        if (!panel || !data) return;
        const titulo = panel.querySelector('.panel-citas-titulo');
        const subt = panel.querySelector('.panel-citas-subtitulo');
        if (titulo) titulo.textContent = 'Citas — ' + data.numero_expediente;
        if (subt) subt.textContent = (data.nombre || '') + (data.edad_texto && data.edad_texto !== '—' ? ' · ' + data.edad_texto : '');
        const prox = panel.querySelector('.tabla-citas-proximas');
        const hist = panel.querySelector('.tabla-citas-historial');
        if (prox) prox.innerHTML = tablaCitasHtml(data.proximas, 'Sin citas programadas');
        if (hist) hist.innerHTML = tablaCitasHtml(data.historial, 'Sin historial de citas');
    }

    function ocultarPanelesCitas() {
        document.querySelectorAll('[data-panel-citas]').forEach(function(p) {
            p.classList.add('oculto');
        });
        pacienteCitasActivoId = null;
    }

    function mostrarPanelCitasEnSeccionActiva() {
        document.querySelectorAll('[data-panel-citas]').forEach(function(p) {
            p.classList.add('oculto');
        });
        const sec = document.querySelector('[id^="sec-"].seccion-activa');
        if (sec && pacienteCitasActivoId) {
            const panel = sec.querySelector('[data-panel-citas]');
            if (panel) panel.classList.remove('oculto');
        }
    }

    async function actualizarCitasPaciente(id) {
        if (!id) {
            ocultarPanelesCitas();
            return;
        }
        pacienteCitasActivoId = String(id);
        try {
            const data = await API.get('/pacientes/' + id + '/citas_resumen/');
            document.querySelectorAll('[data-panel-citas]').forEach(function(panel) {
                renderPanelCitas(panel, data);
            });
            mostrarPanelCitasEnSeccionActiva();
            const panelVisible = document.querySelector('[data-panel-citas]:not(.oculto)');
            if (panelVisible) panelVisible.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } catch (e) {
            ocultarPanelesCitas();
        }
    }

    async function refrescarCitasPacienteActivo() {
        if (pacienteCitasActivoId) {
            await actualizarCitasPaciente(pacienteCitasActivoId);
        }
    }

    async function cargarPacientes() {
        try {
            const data = await API.get('/pacientes/');
            const lista = data.results || data;
            if (!lista.length) {
                document.getElementById('listaPacientes').innerHTML = '<p>No hay pacientes registrados todavía.</p>';
                return;
            }
            renderPacientesTabla(document.getElementById('listaPacientes'), lista, false);
        } catch (e) {
            document.getElementById('listaPacientes').innerHTML = '<p class="texto-error">No se pudieron cargar los datos. Cierre sesión e ingrese de nuevo.</p>';
            Aviso.mostrar(e.message || 'Error al cargar pacientes.');
        }
    }

    function renderPacientesTabla(contenedor, lista, soloLectura, esBusqueda) {
        if (!lista.length) {
            if (esBusqueda) {
                contenedor.innerHTML = '';
                Aviso.pacienteNoExiste();
            } else {
                contenedor.innerHTML = '<p>Sin resultados</p>';
            }
            return;
        }
        let html = '<table class="tabla-sistema"><thead><tr><th>Expediente</th><th>Nombre / Edad</th><th>DPI</th><th>Especialidad</th><th>Estado</th><th></th></tr></thead><tbody>';
        lista.forEach(p => {
            const edad = textoEdadPaciente(p);
            html += '<tr><td>' + p.numero_expediente + '</td>';
            html += '<td class="celda-nombre-edad"><span class="nombre-linea">' + (p.nombre_completo || '') + '</span><span class="edad-linea">' + edad + '</span></td>';
            html += '<td>' + p.dpi + '</td><td>' + (p.especialidad||'') + '</td><td>' + (p.estado_paciente||'') + '</td><td>';
            html += '<button class="btn btn-sm btn-secundario btn-ver" data-id="' + p.id + '">Ver</button> ';
            if (!soloLectura && (rol === 'registros' || rol === 'admin')) {
                html += '<button class="btn btn-sm btn-primario btn-editar" data-id="' + p.id + '">Editar</button>';
            }
            html += '</td></tr>';
        });
        html += '</tbody></table>';
        contenedor.innerHTML = html;
        contenedor.querySelectorAll('.btn-ver, .btn-editar').forEach(btn => {
            btn.onclick = () => {
                document.getElementById('pacienteSeleccionadoId').value = btn.dataset.id;
                if (btn.classList.contains('btn-editar')) abrirFormPaciente(btn.dataset.id);
                else verPaciente(btn.dataset.id);
            };
        });
    }

    async function verPaciente(id) {
        document.getElementById('pacienteSeleccionadoId').value = id;
        await actualizarCitasPaciente(id);
    }

    function asignarValorCampo(el, valor) {
        if (!el) return;
        const v = valor == null ? '' : String(valor);
        if (el.tagName === 'SELECT' && v) {
            const existe = Array.from(el.options).some(function(o) { return o.value === v; });
            if (!existe) {
                const extra = document.createElement('option');
                extra.value = v;
                extra.textContent = v;
                el.appendChild(extra);
            }
        }
        el.value = v;
    }

    function actualizarBotonEliminarPaciente() {
        const btn = document.getElementById('btnEliminarPaciente');
        if (!btn) return;
        const puede = !!pacienteEditId && (rol === 'registros' || rol === 'admin');
        btn.classList.toggle('oculto', !puede);
    }

    async function abrirFormPaciente(id) {
        pacienteEditId = id ? String(id) : null;
        document.getElementById('sec-registros-pacientes').classList.replace('seccion-activa','seccion-oculta');
        document.getElementById('sec-registros-form').classList.replace('seccion-oculta','seccion-activa');
        if (id) {
            const p = await API.get('/pacientes/' + id + '/');
            CAMPOS_PACIENTE.forEach(function(c) {
                asignarValorCampo(document.getElementById('pac_' + c[0]), p[c[0]]);
            });
            document.getElementById('tituloFormPaciente').textContent = 'Editar paciente — ' + p.numero_expediente + ' · ' + (p.nombre_completo || '') + ' (' + textoEdadPaciente(p) + ')';
            actualizarEdadEnFormulario();
            await actualizarCitasPaciente(id);
        } else {
            document.getElementById('formPaciente').reset();
            const est = document.getElementById('pac_estado_paciente');
            if (est) est.value = 'Primera vez';
            document.getElementById('tituloFormPaciente').textContent = 'Nuevo paciente';
            ocultarPanelesCitas();
            actualizarEdadEnFormulario();
        }
        actualizarBotonEliminarPaciente();
    }

    document.getElementById('btnNuevoPaciente').onclick = () => { pacienteEditId = null; abrirFormPaciente(null); };
    document.getElementById('btnCancelarPaciente').onclick = () => {
        pacienteEditId = null;
        ocultarPanelesCitas();
        document.getElementById('sec-registros-form').classList.replace('seccion-activa','seccion-oculta');
        document.getElementById('sec-registros-pacientes').classList.replace('seccion-oculta','seccion-activa');
    };

    const btnRegBuscar = document.getElementById('btnRegistrosBuscar');
    if (btnRegBuscar) {
        btnRegBuscar.onclick = async () => {
            const q = document.getElementById('registrosBuscarQ').value.trim();
            if (!q) { Aviso.mostrar('Escriba nombre o DPI.'); return; }
            const data = await API.get('/registros/buscar/?q=' + encodeURIComponent(q));
            renderPacientesTabla(document.getElementById('listaPacientes'), Array.isArray(data) ? data : [], false, true);
        };
    }
    const btnRegTodos = document.getElementById('btnRegistrosVerTodos');
    if (btnRegTodos) btnRegTodos.onclick = () => cargarPacientes();

    async function eliminarPacienteActual() {
        if (!pacienteEditId) {
            Aviso.mostrar('No hay paciente seleccionado para eliminar.');
            return;
        }
        const id = pacienteEditId;
        let p;
        try {
            p = await API.get('/pacientes/' + id + '/');
        } catch (e) {
            Aviso.mostrar('No se pudo cargar el paciente.');
            return;
        }
        const ok = await Aviso.confirmar(
            '¿Eliminar al paciente ' + p.numero_expediente + ' — ' + (p.nombre_completo || '') +
            '? Se borrarán también sus citas y consultas. Esta acción no se puede deshacer.'
        );
        if (!ok) return;
        try {
            await API.delete('/pacientes/' + id + '/');
            Aviso.mostrar('Paciente eliminado correctamente.');
            pacienteEditId = null;
            actualizarBotonEliminarPaciente();
            document.getElementById('sec-registros-form').classList.replace('seccion-activa', 'seccion-oculta');
            document.getElementById('sec-registros-pacientes').classList.replace('seccion-oculta', 'seccion-activa');
            cargarPacientes();
        } catch (e) {
            Aviso.mostrar(e.message || 'No se pudo eliminar el paciente.');
        }
    }

    const btnEliminarPac = document.getElementById('btnEliminarPaciente');
    if (btnEliminarPac) {
        btnEliminarPac.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            eliminarPacienteActual();
        });
    }

    document.getElementById('btnGuardarPaciente').onclick = async () => {
        const body = {};
        CAMPOS_PACIENTE.forEach(c => {
            const el = document.getElementById('pac_' + c[0]);
            if (el) body[c[0]] = el.value;
        });
        try {
            if (pacienteEditId) await API.patch('/pacientes/' + pacienteEditId + '/', body);
            else await API.post('/pacientes/', body);
            Aviso.mostrar('Guardado correctamente.');
            document.getElementById('btnCancelarPaciente').click();
            cargarPacientes();
        } catch (e) { Aviso.mostrar(e.message); }
    };

    // --- CITAS ---
    let citaEditId = null;

    function llenarSelectEspecialidadesCita() {
        const sel = document.getElementById('citaEspecialidad');
        if (!sel) return;
        sel.innerHTML = '<option value="">-- Seleccionar --</option>';
        (CATALOGOS.especialidades || []).forEach(function(e) {
            const o = document.createElement('option');
            o.value = e;
            o.textContent = e;
            sel.appendChild(o);
        });
    }

    function llenarSelectEspecialidadesMedicoAdmin() {
        const sel = document.getElementById('medicoEspecialidad');
        if (!sel) return;
        sel.innerHTML = '<option value="">-- Seleccionar --</option>';
        (CATALOGOS.especialidades || []).forEach(function(e) {
            const o = document.createElement('option');
            o.value = e;
            o.textContent = e;
            sel.appendChild(o);
        });
    }

    function especialidadEsTarde(especialidad) {
        const lista = (CATALOGOS.especialidades_tarde && CATALOGOS.especialidades_tarde.length)
            ? CATALOGOS.especialidades_tarde
            : ['Psicología Tarde (PST)', 'Medicina General Tarde (MGT)'];
        return !!especialidad && lista.indexOf(especialidad) !== -1;
    }

    function horaAMinutos(horaStr) {
        if (!horaStr) return null;
        const partes = horaStr.split(':');
        const h = parseInt(partes[0], 10);
        const m = parseInt(partes[1] || '0', 10);
        if (isNaN(h) || isNaN(m)) return null;
        return h * 60 + m;
    }

    function aplicarReglaHoraTarde() {
        const sel = document.getElementById('citaEspecialidad');
        const inpHora = document.getElementById('citaHora');
        const ayuda = document.getElementById('citaHoraAyuda');
        if (!sel || !inpHora) return;
        const esTarde = especialidadEsTarde(sel.value);
        if (esTarde) {
            inpHora.min = '12:00';
            if (horaAMinutos(inpHora.value) !== null && horaAMinutos(inpHora.value) < 12 * 60) {
                inpHora.value = '12:00';
            }
            if (ayuda) {
                ayuda.textContent = 'Esta especialidad solo atiende por la tarde. La cita debe ser a partir de las 12:00 p.m.';
            }
        } else {
            inpHora.removeAttribute('min');
            if (ayuda) ayuda.textContent = '';
        }
    }

    function llenarSelectMedicosCita(especialidad, medicoId) {
        const sel = document.getElementById('citaMedico');
        if (!sel) return;
        sel.innerHTML = '<option value="">-- Seleccionar médico --</option>';
        if (!especialidad) {
            sel.innerHTML = '<option value="">-- Seleccione especialidad primero --</option>';
            return;
        }
        const lista = MEDICOS.filter(function(m) {
            return m.activo !== false && m.especialidad === especialidad;
        });
        if (!lista.length) {
            sel.innerHTML = '<option value="">-- Sin médicos en esta especialidad --</option>';
            return;
        }
        lista.forEach(function(m) {
            const o = document.createElement('option');
            o.value = m.id;
            o.textContent = m.nombre;
            sel.appendChild(o);
        });
        if (medicoId) sel.value = String(medicoId);
    }

    function llenarSelectPacientesCita(lista) {
        const sel = document.getElementById('citaPacienteId');
        if (!sel) return;
        const actual = sel.value;
        sel.innerHTML = '<option value="">-- Seleccione paciente --</option>';
        lista.forEach(function(p) {
            const o = document.createElement('option');
            o.value = p.id;
            o.textContent = p.numero_expediente + ' — ' + (p.nombre_completo || p.dpi);
            sel.appendChild(o);
        });
        if (actual) sel.value = actual;
    }

    async function buscarPacientesParaCita() {
        const q = document.getElementById('citaBuscarPaciente').value.trim();
        if (!q) { Aviso.mostrar('Escriba nombre, DPI o expediente.'); return; }
        const data = await API.get('/registros/buscar/?q=' + encodeURIComponent(q));
        if (!data.length) { Aviso.pacienteNoExiste(); return; }
        llenarSelectPacientesCita(data);
        if (data.length === 1) document.getElementById('citaPacienteId').value = data[0].id;
    }

    function abrirFormCita(cita) {
        const caja = document.getElementById('cajaFormCita');
        caja.classList.remove('d-none');
        llenarSelectEspecialidadesCita();
        aplicarLimitesFechas();
        if (cita) {
            citaEditId = cita.id;
            document.getElementById('tituloFormCita').textContent = 'Editar cita';
            llenarSelectPacientesCita([{
                id: cita.paciente,
                numero_expediente: cita.numero_expediente,
                nombre_completo: cita.paciente_nombre,
                dpi: '',
            }]);
            document.getElementById('citaPacienteId').value = cita.paciente;
            document.getElementById('citaFecha').value = cita.fecha;
            document.getElementById('citaHora').value = (cita.hora || '').slice(0, 5);
            document.getElementById('citaEspecialidad').value = cita.especialidad || '';
            llenarSelectMedicosCita(cita.especialidad, cita.medico);
            document.getElementById('citaEstado').value = cita.estado || 'Confirmada';
            document.getElementById('citaNotas').value = cita.notas || '';
        } else {
            citaEditId = null;
            document.getElementById('tituloFormCita').textContent = 'Nueva cita';
            document.getElementById('citaPacienteId').innerHTML = '<option value="">-- Seleccione paciente --</option>';
            document.getElementById('citaBuscarPaciente').value = '';
            document.getElementById('citaFecha').value = hoyISO();
            document.getElementById('citaHora').value = '08:00';
            document.getElementById('citaEspecialidad').value = '';
            llenarSelectMedicosCita('');
            document.getElementById('citaEstado').value = 'Confirmada';
            document.getElementById('citaNotas').value = '';
        }
        aplicarReglaHoraTarde();
    }

    const selCitaEsp = document.getElementById('citaEspecialidad');
    if (selCitaEsp) {
        selCitaEsp.addEventListener('change', function() {
            llenarSelectMedicosCita(this.value);
            aplicarReglaHoraTarde();
        });
    }
    const inpCitaHora = document.getElementById('citaHora');
    if (inpCitaHora) {
        inpCitaHora.addEventListener('change', aplicarReglaHoraTarde);
    }

    function cerrarFormCita() {
        citaEditId = null;
        document.getElementById('cajaFormCita').classList.add('d-none');
    }

    async function cargarCitas() {
        await cargarCatalogos();
        const data = await API.get('/citas/');
        const lista = data.results || data;
        if (!lista.length) {
            document.getElementById('listaCitas').innerHTML = '<p>Sin citas registradas</p>';
            return;
        }
        let html = '<table class="tabla-sistema"><thead><tr><th>Fecha</th><th>Hora</th><th>Expediente</th><th>Paciente</th><th>Especialidad</th><th>Médico</th><th>Estado</th><th></th></tr></thead><tbody>';
        lista.forEach(function(c) {
            html += '<tr><td>' + c.fecha + '</td><td>' + (c.hora || '').slice(0, 5) + '</td><td>' + (c.numero_expediente || '') + '</td><td>' + (c.paciente_nombre || '') + '</td><td>' + c.especialidad + '</td><td>' + (c.medico_nombre || '—') + '</td><td>' + c.estado + '</td><td>';
            if (rol === 'registros' || rol === 'admin') {
                html += '<button type="button" class="btn btn-sm btn-secundario btn-editar-cita" data-id="' + c.id + '">Editar</button> ';
                html += '<button type="button" class="btn btn-sm btn-peligro btn-borrar-cita" data-id="' + c.id + '">Eliminar</button>';
            }
            html += '</td></tr>';
        });
        html += '</tbody></table>';
        document.getElementById('listaCitas').innerHTML = html;

        document.querySelectorAll('.btn-editar-cita').forEach(function(btn) {
            btn.onclick = async function() {
                const c = await API.get('/citas/' + btn.dataset.id + '/');
                abrirFormCita(c);
                document.getElementById('cajaFormCita').scrollIntoView({ behavior: 'smooth' });
            };
        });
        document.querySelectorAll('.btn-borrar-cita').forEach(function(btn) {
            btn.onclick = async function() {
                const okDel = await Aviso.confirmar('¿Eliminar esta cita?');
                if (!okDel) return;
                try {
                    await API.delete('/citas/' + btn.dataset.id + '/');
                    await cargarCitas();
                    await refrescarCitasPacienteActivo();
                } catch (e) { Aviso.mostrar(e.message); }
            };
        });
    }

    const btnNuevaCita = document.getElementById('btnNuevaCita');
    if (btnNuevaCita) btnNuevaCita.onclick = () => abrirFormCita(null);

    const btnCitaBuscar = document.getElementById('btnCitaBuscarPaciente');
    if (btnCitaBuscar) btnCitaBuscar.onclick = buscarPacientesParaCita;

    const btnGuardarCita = document.getElementById('btnGuardarCita');
    if (btnGuardarCita) {
        btnGuardarCita.onclick = async function() {
            const paciente = document.getElementById('citaPacienteId').value;
            const fecha = document.getElementById('citaFecha').value;
            const hora = document.getElementById('citaHora').value;
            const especialidad = document.getElementById('citaEspecialidad').value;
            const medico = document.getElementById('citaMedico').value;
            if (!paciente || !fecha || !hora || !especialidad || !medico) {
                Aviso.mostrar('Complete paciente, fecha, hora, especialidad y médico.');
                return;
            }
            if (fecha < hoyISO()) {
                Aviso.mostrar('La fecha no puede ser anterior a hoy.');
                return;
            }
            if (especialidadEsTarde(especialidad) && horaAMinutos(hora) !== null && horaAMinutos(hora) < 12 * 60) {
                Aviso.mostrar('Las especialidades de la tarde (PST y MGT) solo se pueden agendar a partir de las 12:00 p.m.');
                return;
            }
            const body = {
                paciente: parseInt(paciente, 10),
                medico: parseInt(medico, 10),
                fecha: fecha,
                hora: hora.length === 5 ? hora + ':00' : hora,
                especialidad: especialidad,
                estado: document.getElementById('citaEstado').value,
                notas: document.getElementById('citaNotas').value,
            };
            try {
                if (citaEditId) await API.patch('/citas/' + citaEditId + '/', body);
                else await API.post('/citas/', body);
                if (body.paciente) pacienteCitasActivoId = String(body.paciente);
                Aviso.mostrar('Cita guardada.');
                cerrarFormCita();
                await cargarCitas();
                await refrescarCitasPacienteActivo();
            } catch (e) { Aviso.mostrar(e.message); }
        };
    }

    const btnCancelarCita = document.getElementById('btnCancelarCita');
    if (btnCancelarCita) btnCancelarCita.onclick = cerrarFormCita;

    // --- REGISTRO DIARIO ---
    async function cargarDiario() {
        aplicarLimitesFechas();
        const f = document.getElementById('fechaDiario').value || hoyISO();
        document.getElementById('fechaDiario').value = f;
        const data = await API.get('/registro-diario/?fecha=' + f);
        let html = '<p>Total: ' + (data.registro?.total_pacientes || 0) + '</p>';
        html += '<table class="tabla-sistema"><thead><tr><th>#</th><th>Expediente</th><th>Paciente</th></tr></thead><tbody>';
        (data.detalles || []).forEach(d => {
            html += '<tr><td>' + d.orden + '</td><td>' + d.expediente + '</td><td>' + d.paciente_nombre + '</td></tr>';
        });
        html += '</tbody></table>';
        document.getElementById('detalleDiario').innerHTML = html;
    }

    document.getElementById('btnPdfDiario').onclick = () => {
        const f = document.getElementById('fechaDiario').value;
        if (f > hoyISO()) { Aviso.mostrar('La fecha del registro no puede ser futura.'); return; }
        API.descargarPdfPut('/registro-diario/?fecha=' + f);
    };

    // --- ESTADÍSTICA ---
    async function cargarEstadistica() {
        const data = await API.get('/estadistica/resumen_tablas/');
        let html = '<h3>Pacientes por especialidad</h3>';
        html += tablaDesdeLista(data.pacientes_por_especialidad, ['especialidad','total']);
        html += '<h3>Pacientes por estado</h3>';
        html += tablaDesdeLista(data.pacientes_por_estado, ['estado_paciente','total']);
        html += '<h3>Consultas del mes</h3>';
        html += tablaDesdeLista(data.consultas_mes, ['especialidad','total']);
        document.getElementById('tablasEstadistica').innerHTML = html;
    }

    function tablaDesdeLista(lista, cols) {
        if (!lista || !lista.length) return '<p>Sin datos</p>';
        let h = '<table class="tabla-sistema"><thead><tr>';
        cols.forEach(c => h += '<th>' + c + '</th>');
        h += '</tr></thead><tbody>';
        lista.forEach(row => {
            h += '<tr>';
            cols.forEach(c => h += '<td>' + (row[c] ?? '—') + '</td>');
            h += '</tr>';
        });
        return h + '</tbody></table>';
    }

    document.getElementById('btnExcelEst').onclick = () => {
        fetch(API.base + '/estadistica/exportar_excel/', {
            headers: { 'Authorization': 'Bearer ' + API.token() },
        }).then(r => r.blob()).then(blob => {
            const u = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = u; a.download = 'estadisticas.xlsx'; a.click();
        });
    };

    // --- VAS ---
    async function cargarVAS() {
        const data = await API.get('/vas/');
        const lista = data.results || data;
        let html = '<table class="tabla-sistema"><thead><tr><th>Fecha</th><th>Paciente</th><th>DPI</th><th>Estado</th></tr></thead><tbody>';
        lista.forEach(v => {
            html += '<tr><td>' + v.fecha + '</td><td>' + (v.paciente_nombre||'') + '</td><td>' + (v.dpi||'') + '</td><td>' + v.estado + '</td></tr>';
        });
        html += '</tbody></table>';
        document.getElementById('listaVAS').innerHTML = html;
    }

    document.getElementById('btnNuevoVAS').onclick = async () => {
        const pacienteId = prompt('ID del paciente:');
        const desc = prompt('Descripción del trámite VAS:');
        if (!pacienteId || !desc) return;
        await API.post('/vas/', { paciente: pacienteId, descripcion: desc });
        cargarVAS();
    };

    // --- ADMIN ---
    async function cargarMedicosAdmin() {
        await cargarCatalogos();
        llenarSelectEspecialidadesMedicoAdmin();
        let data;
        try {
            data = await API.get('/medicos/');
        } catch (e) {
            document.getElementById('listaMedicos').innerHTML = '<p>No se pudo cargar la lista.</p>';
            return;
        }
        const lista = data.results || data;
        if (!lista.length) {
            document.getElementById('listaMedicos').innerHTML = '<p>No hay médicos registrados. Agregue al menos uno por especialidad.</p>';
            return;
        }
        let html = '<table class="tabla-sistema"><thead><tr><th>Nombre</th><th>Especialidad</th><th>Activo</th><th></th></tr></thead><tbody>';
        lista.forEach(function(m) {
            html += '<tr><td>' + m.nombre + '</td><td>' + m.especialidad + '</td><td>' + (m.activo ? 'Sí' : 'No') + '</td><td>';
            if (m.activo) {
                html += '<button type="button" class="btn btn-sm btn-secundario btn-desactivar-medico" data-id="' + m.id + '">Desactivar</button>';
            } else {
                html += '<button type="button" class="btn btn-sm btn-primario btn-activar-medico" data-id="' + m.id + '">Activar</button>';
            }
            html += ' <button type="button" class="btn btn-sm btn-peligro btn-borrar-medico" data-id="' + m.id + '">Eliminar</button>';
            html += '</td></tr>';
        });
        html += '</tbody></table>';
        document.getElementById('listaMedicos').innerHTML = html;

        document.querySelectorAll('.btn-desactivar-medico, .btn-activar-medico').forEach(function(btn) {
            btn.onclick = async function() {
                const id = btn.dataset.id;
                const activar = btn.classList.contains('btn-activar-medico');
                try {
                    await API.patch('/medicos/' + id + '/', { activo: activar });
                    await cargarMedicosAdmin();
                    await cargarCatalogos();
                    Aviso.mostrar(activar ? 'Médico activado.' : 'Médico desactivado.');
                } catch (e) { Aviso.mostrar(e.message); }
            };
        });
        document.querySelectorAll('.btn-borrar-medico').forEach(function(btn) {
            btn.onclick = async function() {
                const ok = await Aviso.confirmar('¿Eliminar este médico? No debe tener citas asociadas.');
                if (!ok) return;
                try {
                    await API.delete('/medicos/' + btn.dataset.id + '/');
                    await cargarMedicosAdmin();
                    await cargarCatalogos();
                    Aviso.mostrar('Médico eliminado.');
                } catch (e) { Aviso.mostrar(e.message); }
            };
        });
    }

    const btnGuardarMedico = document.getElementById('btnGuardarMedico');
    if (btnGuardarMedico) {
        btnGuardarMedico.onclick = async function() {
            const nombre = document.getElementById('medicoNombre').value.trim();
            const especialidad = document.getElementById('medicoEspecialidad').value;
            if (!nombre || !especialidad) {
                Aviso.mostrar('Indique nombre y especialidad del médico.');
                return;
            }
            try {
                await API.post('/medicos/', { nombre: nombre, especialidad: especialidad, activo: true });
                document.getElementById('medicoNombre').value = '';
                await cargarMedicosAdmin();
                await cargarCatalogos();
                Aviso.mostrar('Médico registrado correctamente.');
            } catch (e) { Aviso.mostrar(e.message); }
        };
    }

    const btnCrearUsuario = document.getElementById('btnCrearUsuario');
    if (btnCrearUsuario) {
        btnCrearUsuario.onclick = async function() {
            const username = document.getElementById('usuarioNuevoUsername').value.trim();
            const password = document.getElementById('usuarioNuevoPassword').value;
            const rolNuevo = document.getElementById('usuarioNuevoRol').value;
            if (!username || !password) {
                Aviso.mostrar('Indique usuario y contraseña.');
                return;
            }
            try {
                await API.post('/usuarios/', { username: username, password: password, rol: rolNuevo });
                document.getElementById('usuarioNuevoUsername').value = '';
                document.getElementById('usuarioNuevoPassword').value = '';
                cargarUsuarios();
                Aviso.mostrar('Usuario creado correctamente.');
            } catch (e) { Aviso.mostrar(e.message); }
        };
    }

    async function initVerBaseDatos() {
        const div = document.getElementById('adminBdResumen');
        if (!div) return;
        div.innerHTML = '<p>Cargando resumen…</p>';
        try {
            const [pac, cit, med, usr, bit] = await Promise.all([
                API.get('/pacientes/'),
                API.get('/citas/'),
                API.get('/medicos/'),
                API.get('/usuarios/'),
                API.get('/bitacora/?page_size=5'),
            ]);
            const n = function(d) { return (d && d.count != null) ? d.count : (Array.isArray(d) ? d.length : (d.results || []).length); };
            let html = '<table class="tabla-sistema"><thead><tr><th>Tabla</th><th>Registros</th></tr></thead><tbody>';
            html += '<tr><td>Pacientes</td><td>' + n(pac) + '</td></tr>';
            html += '<tr><td>Citas</td><td>' + n(cit) + '</td></tr>';
            html += '<tr><td>Médicos</td><td>' + n(med) + '</td></tr>';
            html += '<tr><td>Usuarios</td><td>' + n(usr) + '</td></tr>';
            html += '<tr><td>Bitácora</td><td>' + n(bit) + '</td></tr>';
            html += '</tbody></table>';
            div.innerHTML = html;
        } catch (e) {
            div.innerHTML = '<p class="texto-error">Error al leer datos: ' + (e.message || '') + '</p>';
        }
    }

    async function cargarUsuarios() {
        const data = await API.get('/usuarios/');
        const lista = data.results || data;
        const miId = sessionStorage.getItem('user_id');
        let html = '<table class="tabla-sistema"><thead><tr><th>Usuario</th><th>Rol</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>';
        lista.forEach(function(u) {
            const esYo = miId && String(u.id) === String(miId);
            html += '<tr><td>' + u.username + '</td><td>' + u.rol + '</td><td>' + (u.estado || '') + '</td><td class="celda-acciones-usuario">';
            html += '<button type="button" class="btn btn-sm btn-secundario btn-ver-usuario" data-id="' + u.id + '">Ver datos</button> ';
            if (!esYo) {
                if (u.estado === 'Activo') {
                    html += '<button type="button" class="btn btn-sm btn-peligro btn-bloquear-usuario" data-id="' + u.id + '" data-nombre="' + u.username + '">Bloquear</button> ';
                } else {
                    html += '<button type="button" class="btn btn-sm btn-primario btn-reactivar-usuario" data-id="' + u.id + '">Reactivar</button> ';
                }
                html += '<button type="button" class="btn btn-sm btn-peligro btn-eliminar-usuario" data-id="' + u.id + '" data-nombre="' + u.username + '">Eliminar</button>';
            } else {
                html += '<span class="texto-ayuda">(su cuenta)</span>';
            }
            html += '</td></tr>';
        });
        html += '</tbody></table>';
        document.getElementById('listaUsuarios').innerHTML = html;

        document.querySelectorAll('.btn-ver-usuario').forEach(function(btn) {
            btn.onclick = function() { verDatosUsuario(btn.dataset.id); };
        });
        document.querySelectorAll('.btn-bloquear-usuario').forEach(function(btn) {
            btn.onclick = async function() {
                const ok = await Aviso.confirmar('¿Bloquear al usuario ' + btn.dataset.nombre + '?');
                if (!ok) return;
                try {
                    await API.post('/usuarios/' + btn.dataset.id + '/bloquear/', {});
                    cargarUsuarios();
                    Aviso.mostrar('Usuario bloqueado.');
                } catch (e) { Aviso.mostrar(e.message); }
            };
        });
        document.querySelectorAll('.btn-reactivar-usuario').forEach(function(btn) {
            btn.onclick = async function() {
                try {
                    await API.post('/usuarios/' + btn.dataset.id + '/reactivar/', {});
                    cargarUsuarios();
                    Aviso.mostrar('Usuario reactivado.');
                } catch (e) { Aviso.mostrar(e.message); }
            };
        });
        document.querySelectorAll('.btn-eliminar-usuario').forEach(function(btn) {
            btn.onclick = async function() {
                const ok = await Aviso.confirmar('¿Eliminar al usuario ' + btn.dataset.nombre + '? Esta acción no se puede deshacer.');
                if (!ok) return;
                try {
                    await API.delete('/usuarios/' + btn.dataset.id + '/');
                    cargarUsuarios();
                    Aviso.mostrar('Usuario eliminado.');
                } catch (e) { Aviso.mostrar(e.message); }
            };
        });
    }

    async function verDatosUsuario(id) {
        const pwd = await Aviso.pedirContrasena('Ingrese su contraseña de administrador para ver los datos del usuario.');
        if (!pwd) return;
        try {
            const data = await API.post('/usuarios/' + id + '/ver_datos/', { contrasena_admin: pwd });
            const clave = data.clave_referencia || 'No registrada';
            Aviso.mostrar(
                'Usuario: ' + data.username +
                '\nContraseña: ' + clave +
                '\nRol: ' + data.rol +
                '\nEstado: ' + data.estado
            );
        } catch (e) { Aviso.mostrar(e.message); }
    }

    async function cargarBitacora() {
        const data = await API.get('/bitacora/');
        const lista = data.results || data;
        let html = '<table class="tabla-sistema"><thead><tr><th>Fecha</th><th>Usuario</th><th>Acción</th><th>Detalle</th></tr></thead><tbody>';
        lista.forEach(b => {
            html += '<tr><td>' + b.fecha + '</td><td>' + b.usuario + '</td><td>' + b.accion + '</td><td>' + (b.detalle||'') + '</td></tr>';
        });
        html += '</tbody></table>';
        document.getElementById('listaBitacora').innerHTML = html;
    }

    document.getElementById('btnRespaldo').onclick = async () => {
        const r = await API.post('/respaldo/', {});
        Aviso.mostrar(r.mensaje + ' — ' + r.registros + ' pacientes.');
    };

    document.addEventListener('DOMContentLoaded', aplicarLimitesFechas);
    aplicarLimitesFechas();

})();

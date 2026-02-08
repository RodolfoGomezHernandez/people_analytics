    # PROYECTO AURORA AUSTRALIS - PEOPLE ANALYTICS
**Estado:** Fase Beta (Desarrollo)
**Versión:** 0.2.0
**Fecha de Actualización:** 06/02/2026

## 1. Módulos Activos
### A. Core (Administración)
- Panel administrativo (Django Admin) habilitado.
- Gestión de usuarios y permisos básica.

### B. Reclutamiento (Bot WhatsApp)
- **Tecnología:** Twilio Sandbox + Django Webhook.
- **Flujo:** Mensajería bidireccional basada en texto (sin imágenes por restricciones de cuota).
- **Funcionalidades:**
  - Máquina de estados (FSM) para guiar al candidato paso a paso.
  - Validación de RUT chileno con algoritmo Módulo 11 (Matemática real).
  - Normalización de nombres (Mayúsculas sin tildes).
  - Persistencia de datos en modelo `Candidato`.
- **Seguridad:** Credenciales extraídas a `settings.py`.

## 2. Arquitectura Técnica
- **Backend:** Django 5.x (Python).
- **Base de Datos:** SQLite (Dev) / PostgreSQL (Prod - Pendiente).
- **Túnel:** Ngrok (para exposición local de Webhooks).
- **Seguridad:** CSRF Exempt en webhooks, validación de Host.

## 3. Próximos Pasos (Roadmap)
- [ ] Conectar repositorio a GitHub (Prioridad Alta).
- [ ] Crear Nuevo Módulo Urgente (Prioridad Alta).
- [ ] Migrar DB a PostgreSQL.
- [ ] Implementar Docker para despliegue.

# 🚛 Sistema de Gestión de Transporte - Aurora Australis

Módulo para el control de flota, costos y asistencia de transporte de personal.

## 📊 Dashboard de Analytics
El sistema cuenta con un dashboard avanzado para la toma de decisiones:
- **8 KPIs en tiempo real:** Evolución de costos, Costo por Ruta, Ocupación y CPP (Costo Por Pasajero).
- **Filtros Persistentes:** El sistema "recuerda" el rango de fechas seleccionado aunque cambies de página.
- **Gráficos Interactivos:** Visualización con Chart.js (Curvas sin relleno, Donas, Barras horizontales).
- **Paginación Inteligente:** Navegación optimizada para grandes volúmenes de datos.

## 🛠 Carga Masiva de Datos
El sistema incluye un script inteligente para importar históricos desde Excel, capaz de limpiar y normalizar datos sucios.

**Comando:**
```bash
python manage.py cargar_historico nombre_archivo.xlsx
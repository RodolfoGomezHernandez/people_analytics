DOCUMENTO MAESTRO: PROYECTO AURORA ANALYTICS (V1.0)
Propósito del Proyecto: Sistema integral para "Aurora Australis S.A." que centraliza People Analytics, Automatización de Reclutamiento, Control de Asistencia (GREX) y Gestión de Servicios (Casino/Transporte).

Tecnologías:

Backend: Python 3.13 + Django 5/6.

Base de Datos: SQLite (Desarrollo) / PostgreSQL (Futuro Producción).

Frontend: HTML5 + TailwindCSS + Chart.js.

Integraciones: Lectura de Excel/CSV (Pandas), WhatsApp API (Futuro).

Estructura de Datos Actual (Modelos Clave):

Colaborador: Maestro de empleados. Datos: RUT, Nombres, Cargo, Área, Sección, Turno (clave para reglas), Estado.

Marcaje: Historial de entradas/salidas. Vinculado a Colaborador. Fuente: Reloj control (GREX).

ReglaAsistencia: Configuración lógica. Define horarios teóricos, tiempos de colación y holguras por Área o Palabra Clave de Turno.

Anomalia: Resultado del algoritmo de auditoría. Tipos: FALTA, ATRASO, EXCESO_COLACION. Métrica clave: minutos_perdidos.

Funcionalidades Implementadas:

ETL de Fichas: Carga masiva desde Excel de dotación. Normalización de RUTs.

ETL de Asistencia: Carga masiva de reloj control. Detección automática de fechas y formatos.

Motor de Análisis (utils.py):

Algoritmo inteligente que cruza Colaborador vs ReglaAsistencia usando lógica difusa (inclusión de texto para Áreas y Turnos).

Detecta automáticamente si es Turno de Noche (cruce de día).

Calcula atrasos y excesos de colación en minutos exactos.

Reportes: Vista semanal con KPIs de horas perdidas y costo estimado. Gráficos de distribución por tipo de falta y área crítica.

Pendientes / Roadmap:

Refactorización: Separar lógica en apps (core, asistencia, reclutamiento).

Reclutamiento: Bot de WhatsApp para captura de documentos y selfies. Sistema de solicitud de dotación para gerentes.

Servicios: Módulo de Casino y Buses.

IA: Predicción de ausentismo.
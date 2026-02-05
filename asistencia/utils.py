import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from django.db.models import Q
from asistencia.models import Colaborador, Marcaje, ReglaAsistencia, Anomalia

# ==========================================
# 1. IMPORTADOR DE FICHAS (PERSONAS)
# ==========================================
def importar_fichas_grex(archivo):
    try:
        if archivo.name.lower().endswith('.csv'):
            df_raw = pd.read_csv(archivo, header=None, sep=None, engine='python', encoding='latin-1')
        else:
            df_raw = pd.read_excel(archivo, header=None)
    except Exception as e:
        raise Exception(f"No se pudo leer el archivo: {e}")

    header_idx = None
    for i, row in df_raw.iterrows():
        if row.astype(str).str.contains('RUT').any():
            header_idx = i
            break
    
    if header_idx is None:
        raise Exception("No se encontró la columna 'RUT'.")

    df = df_raw.iloc[header_idx + 1:].copy()
    df.columns = df_raw.iloc[header_idx].astype(str).str.strip().str.upper()
    df = df.replace({np.nan: None})

    c_creados = 0
    c_actualizados = 0

    for _, row in df.iterrows():
        rut_raw = str(row.get('RUT', '')).strip()
        if not rut_raw or rut_raw in ['None', 'nan', '']:
            continue

        obj, created = Colaborador.objects.update_or_create(
            rut=rut_raw,
            defaults={
                'nombres': row.get('NOMBRES'),
                'apellido_paterno': row.get('PRIMER APELLIDO'),
                'area': row.get('ÁREA'),
                'seccion': row.get('SECCIÓN'),
                'cargo': row.get('CARGO'),
                'estado_ficha': row.get('ESTADO FICHA', 'Vigente'),
                'turno': row.get('TURNO', '') # Guardamos el texto del turno para las reglas
            }
        )
        if created: c_creados += 1
        else: c_actualizados += 1
        
    return c_creados, c_actualizados

# ==========================================
# 2. IMPORTADOR DE ASISTENCIA (MARCAJES)
# ==========================================
def importar_asistencia_grex(archivo):
    try:
        if archivo.name.lower().endswith('.csv'):
            df_raw = pd.read_csv(archivo, header=None, sep=None, engine='python', encoding='latin-1')
        else:
            df_raw = pd.read_excel(archivo, header=None)
    except Exception as e:
        raise Exception(f"Error lectura: {e}")

    header_idx = None
    for i, row in df_raw.iterrows():
        s = row.astype(str).str.upper()
        if s.str.contains('MOVIMIENTO').any() and s.str.contains('RUT').any():
            header_idx = i
            break
            
    if header_idx is None:
        raise Exception("No se encontró columna 'MOVIMIENTO' o 'RUT'")

    df = df_raw.iloc[header_idx + 1:].copy()
    df.columns = df_raw.iloc[header_idx].astype(str).str.strip().str.upper()
    df = df.replace({np.nan: None})

    nuevos = 0
    no_encontrados = 0

    for index, row in df.iterrows():
        rut_excel = str(row.get('RUT', '')).strip()
        fecha_str = str(row.get('FECHA', '')).strip()
        hora_str = str(row.get('HORA', '')).strip()
        
        if not rut_excel or len(rut_excel) < 3: continue

        try:
            colaborador = Colaborador.objects.get(rut=rut_excel)
        except Colaborador.DoesNotExist:
            no_encontrados += 1
            continue

        # Lógica Robusta de Fecha
        fecha_obj = None
        try:
            if isinstance(row.get('FECHA'), (datetime, pd.Timestamp)):
                fecha_obj = row.get('FECHA').date()
            else:
                for fmt in ('%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d'):
                    try:
                        fecha_obj = datetime.strptime(fecha_str, fmt).date()
                        break
                    except ValueError: continue
            
            if not fecha_obj: continue
        except:
            continue

        # Crear Marcaje
        try:
            _, created = Marcaje.objects.get_or_create(
                colaborador=colaborador,
                fecha=fecha_obj,
                hora=hora_str,
                defaults={
                    'tipo_movimiento': row.get('MOVIMIENTO'),
                    'dispositivo': row.get('CÓDIGO DISPOSITIVO')
                }
            )
            if created: nuevos += 1
        except:
            pass

    return nuevos, no_encontrados

# ==========================================
# 3. MOTOR DE ANÁLISIS (REGLAS Y ANOMALÍAS)
# ==========================================


def analizar_asistencia_dia(fecha_analisis):
    # print(f"Analizando {fecha_analisis}...") # Opcional para no saturar la consola
    
    colaboradores = Colaborador.objects.filter(estado_ficha__icontains='Vigente')
    todas_las_reglas = list(ReglaAsistencia.objects.all())
    
    if not todas_las_reglas: return 0

    # Limpieza preventiva: Borrar anomalías de ese día para recalcular desde cero
    Anomalia.objects.filter(fecha=fecha_analisis).delete()
    
    anomalias_creadas = 0

    for colab in colaboradores:
        # --- A. BUSCADOR DE REGLA (Misma lógica anterior) ---
        area_colab = str(colab.area).strip().upper() if colab.area else ""
        turno_colab = str(colab.turno).strip().upper() if colab.turno else ""
        
        regla_aplicar = None
        candidatas = []

        # Filtro por Área (Flexible)
        for r in todas_las_reglas:
            area_regla = str(r.area).strip().upper() if r.area else ""
            if not area_regla or area_regla in area_colab:
                candidatas.append(r)
        
        # Filtro por Turno
        if candidatas:
            for cand in candidatas:
                clave = str(cand.palabra_clave_turno).strip().upper() if cand.palabra_clave_turno else ""
                if clave and clave in turno_colab:
                    regla_aplicar = cand
                    break
            if not regla_aplicar:
                # Si no hay match de turno, buscar la genérica (sin palabra clave)
                for cand in candidatas:
                    if not cand.palabra_clave_turno:
                        regla_aplicar = cand
                        break
        
        # Fallback final: Si sigue sin regla, forzar la primera candidata disponible
        if not regla_aplicar and candidatas:
            regla_aplicar = candidatas[0]

        if not regla_aplicar: continue

        # --- B. ANÁLISIS ---
        inicio = datetime.combine(fecha_analisis, datetime.min.time())
        fin = datetime.combine(fecha_analisis, datetime.max.time())
        if regla_aplicar.es_turno_noche:
            fin = fin + timedelta(days=1)

        marcajes = Marcaje.objects.filter(colaborador=colab, fecha__range=[inicio.date(), fin.date()]).order_by('fecha', 'hora')
        times = [datetime.combine(m.fecha, m.hora) for m in marcajes]

        # 1. Ausencia (Usamos update_or_create para evitar IntegrityError)
        if not times:
            # Solo marcar falta si no es fin de semana (Lógica simple: 5=Sábado, 6=Domingo)
            if fecha_analisis.weekday() < 5: 
                Anomalia.objects.update_or_create(
                    colaborador=colab, fecha=fecha_analisis, tipo='FALTA',
                    defaults={'minutos_perdidos': 480}
                )
                anomalias_creadas += 1
            continue

        # 2. Atraso
        entrada_real = times[0]
        entrada_teorica = datetime.combine(fecha_analisis, regla_aplicar.entrada_teorica)
        if regla_aplicar.es_turno_noche and entrada_real.hour < 12:
             entrada_teorica += timedelta(days=1)

        diff_entrada = (entrada_real - entrada_teorica).total_seconds() / 60
        if diff_entrada > regla_aplicar.holgura_minutos:
            Anomalia.objects.update_or_create(
                colaborador=colab, fecha=fecha_analisis, tipo='ATRASO',
                defaults={
                    'detalle': f"Entró {entrada_real.strftime('%H:%M')}",
                    'minutos_perdidos': int(diff_entrada)
                }
            )
            anomalias_creadas += 1
            
        # 3. Colación
        if len(times) >= 4:
            delta_col = (times[2] - times[1]).total_seconds() / 60
            if delta_col > (regla_aplicar.tiempo_maximo_colacion + regla_aplicar.holgura_minutos):
                exceso = int(delta_col - regla_aplicar.tiempo_maximo_colacion)
                Anomalia.objects.update_or_create(
                    colaborador=colab, fecha=fecha_analisis, tipo='EXCESO_COLACION',
                    defaults={
                        'detalle': f"Tomó {int(delta_col)} min",
                        'minutos_perdidos': exceso
                    }
                )
                anomalias_creadas += 1

    return anomalias_creadas
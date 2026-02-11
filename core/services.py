import pandas as pd
from django.db import transaction
from dotacion.models import Colaborador
from asistencia.models import RegistroAsistencia, Anomalia

def normalizar_rut(rut_raw):
    """Elimina puntos y espacios del RUT para estandarizar."""
    if not rut_raw or pd.isna(rut_raw):
        return None
    return str(rut_raw).replace('.', '').strip().upper()

def parse_fecha(fecha_raw):
    """Intenta convertir fechas de Excel a formato Python Date"""
    if pd.isna(fecha_raw): return None
    try:
        # Intenta parsear formato string 'dd-mm-yyyy' o timestamp de Excel
        return pd.to_datetime(fecha_raw, dayfirst=True).date()
    except:
        return None

def procesar_archivo_dotacion(carga_instance):
    try:
        # Header en fila 9 (Fila 10 real) según tu Excel
        df = pd.read_excel(carga_instance.archivo.path, engine='openpyxl', header=9)
        df.columns = [str(c).strip().upper() for c in df.columns] # Normalizar cabeceras a mayúsculas
    except Exception as e:
        raise Exception(f"Error lectura Excel: {e}")

    registros_creados = 0
    registros_actualizados = 0

    with transaction.atomic():
        for index, row in df.iterrows():
            # 1. RUT (Clave)
            rut_limpio = normalizar_rut(row.get('RUT'))
            if not rut_limpio: continue 

            # 2. Construcción de Nombre
            nombres = str(row.get('NOMBRES', '')).strip()
            paterno = str(row.get('PATERNO', '')).strip()
            materno = str(row.get('MATERNO', '')).strip()
            # Limpieza de 'nan'
            if nombres == 'nan': nombres = ''
            if paterno == 'nan': paterno = ''
            if materno == 'nan': materno = ''
            
            nombre_completo = f"{nombres} {paterno} {materno}".strip()

            # 3. Mapeo de Campos Extendidos (Según tu CSV)
            defaults = {
                'nombre_completo': nombre_completo,
                'cargo': str(row.get('CARGO', '')).replace('nan', ''),
                'centro_costo': str(row.get('CENTRO COSTO') or row.get('CENTRO DE COSTO', '')).replace('nan', ''),
                
                # Fechas
                'fecha_ingreso': parse_fecha(row.get('FECHA DE INGRESO') or row.get('FECHA INGRESO')),
                'fecha_nacimiento': parse_fecha(row.get('FECHA NACIMIENTO')),
                
                # Demográficos
                'sexo': str(row.get('SEXO', '')).replace('nan', ''),
                'nacionalidad': str(row.get('NACIONALIDAD', '')).replace('nan', ''),
                'comuna': str(row.get('COMUNA', '')).replace('nan', ''),
                'direccion': str(row.get('DIRECCION') or row.get('DIRECCIÓN', '')).replace('nan', ''),
                
                # Perfil
                'escolaridad': str(row.get('ESCOLARIDAD', '')).replace('nan', ''),
                'email': str(row.get('EMAIL') or row.get('CORREO', '')).replace('nan', ''),
                'telefono': str(row.get('TELEFONO') or row.get('FONO', '')).replace('nan', ''),
                
                # Lógica 'Recomendable' (Si dice 'No' es False, cualquier otra cosa True)
                'es_recomendable': False if str(row.get('RECOMENDABLE', '')).upper() == 'NO' else True,
                
                'activo': True
            }

            # 4. Upsert (Actualizar o Crear)
            obj, created = Colaborador.objects.update_or_create(
                rut=rut_limpio,
                defaults=defaults
            )

            if created:
                registros_creados += 1
            else:
                registros_actualizados += 1

    carga_instance.log_errores = f"Carga Completa. Nuevos: {registros_creados} | Actualizados: {registros_actualizados}"
    carga_instance.procesado = True
    carga_instance.save()
    """
    Lee el archivo FICHAS (Dotación) desde la fila 9 (header).
    """
    # header=9 significa que la fila 10 del Excel contiene los títulos (0-indexed en Python)
    df = pd.read_excel(carga_instance.archivo.path, engine='openpyxl', header=9)
    
    registros_creados = 0
    registros_actualizados = 0

    with transaction.atomic():
        for index, row in df.iterrows():
            # 1. Obtenemos el RUT
            rut_limpio = normalizar_rut(row.get('RUT'))
            
            # Si no hay RUT válido, saltamos la fila (puede ser fila vacía al final)
            if not rut_limpio:
                continue

            # 2. Construimos el nombre completo (Paterno + Materno + Nombres)
            paterno = str(row.get('PATERNO', '')).strip()
            materno = str(row.get('MATERNO', '')).strip()
            nombres = str(row.get('NOMBRES', '')).strip()
            
            # Manejo de valores 'nan' que pandas genera para celdas vacías
            if paterno == 'nan': paterno = ''
            if materno == 'nan': materno = ''
            if nombres == 'nan': nombres = ''

            nombre_completo = f"{nombres} {paterno} {materno}".strip()

            # 3. Datos adicionales
            cargo = row.get('CARGO')
            if pd.isna(cargo): cargo = 'Sin Cargo'

            centro_costo = row.get('CENTRO COSTO') 
            if pd.isna(centro_costo): centro_costo = 'Sin CC'

            # Preparamos el diccionario de datos
            defaults = {
                'nombre_completo': nombre_completo,
                'cargo': str(cargo),
                'centro_costo': str(centro_costo),
                'activo': True # Asumimos que si viene en el reporte, está activo
            }

            # 4. Guardar en Base de Datos
            obj, created = Colaborador.objects.update_or_create(
                rut=rut_limpio,
                defaults=defaults
            )

            if created:
                registros_creados += 1
            else:
                registros_actualizados += 1

    # Guardamos el resumen en el log de la carga
    carga_instance.log_errores = f"Proceso OK. Nuevos: {registros_creados}, Actualizados: {registros_actualizados}"
    carga_instance.procesado = True
    carga_instance.save()

def procesar_archivo_asistencia(carga_instance):
    
    """
    Lee el archivo ESTADÍA (Asistencia). 
    NOTA: Debemos verificar si este archivo también tiene filas basura al inicio.
    Por defecto asumo header=0, pero si es igual al de fichas, avísame.
    """
    df = pd.read_excel(carga_instance.archivo.path, engine='openpyxl') # Ajustar header si es necesario
    
    registros_creados = 0
    errores = []

    with transaction.atomic():
        for index, row in df.iterrows():
            rut_raw = row.get('RUT') or row.get('rut')
            rut_limpio = normalizar_rut(rut_raw)
            
            if not rut_limpio: continue

            # Buscamos al empleado
            try:
                colaborador = Colaborador.objects.get(rut=rut_limpio)
            except Colaborador.DoesNotExist:
                # Opcional: No llenar el log de errores si falta gente, o crear un warning
                # errores.append(f"Fila {index}: RUT {rut_limpio} no existe en Dotación.")
                continue

            # Parsear fechas y horas (Ajustar nombres de columnas según tu archivo de Estadía)
            fecha_excel = row.get('Fecha') 
            hora_ent = row.get('Entrada Real')
            hora_sal = row.get('Salida Real')
            
            # Validación simple de fecha
            if pd.isna(fecha_excel):
                continue

            # Crear registro
            registro, created = RegistroAsistencia.objects.get_or_create(
                colaborador=colaborador,
                fecha=fecha_excel,
                defaults={
                    'hora_entrada': hora_ent if pd.notnull(hora_ent) else None,
                    'hora_salida': hora_sal if pd.notnull(hora_sal) else None,
                    'archivo_origen': carga_instance
                }
            )
            
            if created:
                registros_creados += 1

    resumen = f"Cargados: {registros_creados}. "
    if errores:
        resumen += f"Alertas: {len(errores)} Ruts no encontrados."
    
    carga_instance.log_errores = resumen
    carga_instance.procesado = True
    carga_instance.save()
import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from transporte.models import Vehiculo, Ruta, Conductor, RegistroSalida
from django.contrib.auth.models import User
from datetime import datetime, time

class Command(BaseCommand):
    help = 'Carga masiva con estandarización agresiva de rutas y limpieza de datos'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Ruta del archivo Excel')

    def normalizar_ruta(self, valor_celda):
        """
        Transforma nombres sucios en nombres estándar.
        Ej: "CURICÓ 1,2,3" -> "CURICO 1"
            "TENO 1 VAN APOYO" -> "TENO 1"
        """
        if pd.isna(valor_celda) or str(valor_celda).strip() == '':
            return None

        # 1. LIMPIEZA BÁSICA (Mayúsculas y sin tildes)
        nombre = str(valor_celda).upper().strip()
        nombre = nombre.replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')

        # 2. REGLAS DE NEGOCIO (Busca palabras clave y asigna la ruta estándar)
        
        # --- CASO CURICO ---
        if "CURICO" in nombre:
            # Si contiene "1" (ej: "CURICO 1", "CURICO 1,2,3"), forzamos CURICO 1
            if "1" in nombre: return "CURICO 1"
            # Si no tiene 1 pero tiene 2 (ej: "CURICO 2,3"), forzamos CURICO 2
            if "2" in nombre: return "CURICO 2"
            # Si solo tiene 3
            if "3" in nombre: return "CURICO 3"
            # Si dice solo "CURICO" sin número, asumimos 1
            return "CURICO 1"

        # --- CASO TENO ---
        if "TENO" in nombre:
            # TENO CENTRO lo mandamos a TENO 1 (o crea una regla aparte si prefieres)
            if "CENTRO" in nombre: return "TENO 1"
            if "2" in nombre: return "TENO 2"
            # Atrapa "TENO 1", "TENO 1 VAN", "TENO 1 APOYO"
            return "TENO 1"

        # --- CASO LA MONTAÑA ---
        # Aceptamos MONTAÑA con Ñ o N por si acaso
        if "MONTANA" in nombre or "MONTAÑA" in nombre:
            if "2" in nombre: return "LA MONTAÑA 2"
            return "LA MONTAÑA 1"

        # --- OTROS CASOS SIMPLES ---
        if "MOLINA" in nombre: return "MOLINA"
        if "MORZA" in nombre: return "MORZA"
        if "RAUCO" in nombre: return "RAUCO"
        if "CHEPICA" in nombre: return "CHEPICA"

        # Si no coincide con nada conocido, devolvemos el nombre limpio pero original
        # (Esto sirve para detectar rutas nuevas en el futuro)
        return nombre

    def handle(self, *args, **kwargs):
        file_path = kwargs['excel_file']
        print(f"--- INICIANDO CARGA CON LIMPIEZA PROFUNDA ---")

        try:
            # Leemos el Excel
            df = pd.read_excel(file_path)
            
            # Normalizamos encabezados (quita espacios y pone mayúsculas)
            df.columns = df.columns.astype(str).str.upper().str.strip()
            
            print(f"Columnas encontradas: {list(df.columns)}")

        except Exception as e:
            print(f"❌ Error crítico leyendo el archivo: {e}")
            return

        # 1. RELLENAR CELDAS VACÍAS (MERGED CELLS)
        # Esto soluciona el problema de que la fecha solo aparece en la primera fila del día
        df['FECHA'] = df['FECHA'].ffill()
        df['TURNO'] = df['TURNO'].ffill()

        # Generamos recursos base
        user_sys, _ = User.objects.get_or_create(username='sistema_carga')
        chofer_gen, _ = Conductor.objects.get_or_create(rut='9999999-9', defaults={'nombre': 'CHOFER HISTÓRICO'})

        # Cache para optimizar velocidad
        cache_rutas = {}
        cache_vehiculos = {}
        
        registros_creados = 0
        errores = 0

        for index, row in df.iterrows():
            try:
                # A. LIMPIEZA DE RUTA
                # Si la celda ruta está vacía, saltamos la fila (puede ser fila de totales)
                ruta_raw = row.get('RUTA')
                ruta_final = self.normalizar_ruta(ruta_raw)
                
                if not ruta_final: 
                    continue # Salta filas vacías

                # B. LIMPIEZA DE FECHA Y HORA
                fecha_excel = row['FECHA']
                turno_str = str(row['TURNO']).upper()
                
                # Definir hora según turno
                hora_viaje = time(8, 0) # Default
                if 'TURNO 1' in turno_str: hora_viaje = time(7, 30) # Mañana
                elif 'TURNO 2' in turno_str: hora_viaje = time(16, 30) # Tarde
                elif 'TURNO 3' in turno_str: hora_viaje = time(23, 30) # Noche

                # Combinar fecha y hora
                if not isinstance(fecha_excel, datetime):
                    # Intenta parsear texto dd-mm-yyyy
                    fecha_excel = pd.to_datetime(fecha_excel, dayfirst=True)
                
                fecha_completa = timezone.make_aware(datetime.combine(fecha_excel.date(), hora_viaje))

                # C. LIMPIEZA DE TARIFA Y PAX
                # Tarifa: Quitar $, puntos y convertir a int
                try:
                    tarifa_str = str(row['TARIFA']).replace('$', '').replace('.', '').replace(' ', '')
                    tarifa = int(float(tarifa_str))
                except:
                    tarifa = 0

                # Pax: Convertir a int, si es vacío o texto raro es 0
                try:
                    pax = int(row['PAX'])
                except:
                    pax = 0

                # D. IDENTIFICAR VEHÍCULO
                tipo_str = str(row['TIPO']).upper()
                if 'MINIBUS' in tipo_str:
                    modelo, cap, pat = 'MINIBUS', 25, 'HIST-MINI'
                elif 'VAN' in tipo_str:
                    modelo, cap, pat = 'VAN', 17, 'HIST-VAN'
                else:
                    modelo, cap, pat = 'BUS', 42, 'HIST-BUS'

                # E. GESTIÓN DE OBJETOS EN BD (Con Cache)
                
                # Vehículo
                if pat not in cache_vehiculos:
                    v, _ = Vehiculo.objects.get_or_create(patente=pat, defaults={'tipo': modelo, 'capacidad': cap})
                    cache_vehiculos[pat] = v
                
                # Ruta (Usando el nombre ya LIMPIO)
                if ruta_final not in cache_rutas:
                    r, _ = Ruta.objects.get_or_create(
                        nombre=ruta_final, 
                        defaults={'origen': 'Planta', 'destino': ruta_final}
                    )
                    cache_rutas[ruta_final] = r

                # F. GUARDAR
                RegistroSalida.objects.create(
                    fecha_registro=fecha_completa,
                    registrado_por=user_sys,
                    ruta=cache_rutas[ruta_final],
                    vehiculo=cache_vehiculos[pat],
                    conductor=chofer_gen,
                    cantidad_pasajeros=pax,
                    valor_viaje=tarifa
                )
                registros_creados += 1

            except Exception as e:
                # print(f"Fila {index} saltada: {e}") # Descomentar para debug
                errores += 1

        print(f"✅ PROCESO TERMINADO")
        print(f"   - Registros importados: {registros_creados}")
        print(f"   - Filas ignoradas/errores: {errores}")
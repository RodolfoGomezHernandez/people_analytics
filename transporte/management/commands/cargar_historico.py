import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from transporte.models import Vehiculo, Ruta, Conductor, RegistroSalida
from django.contrib.auth.models import User
from datetime import datetime, time

class Command(BaseCommand):
    help = 'Carga datos históricos con normalización de rutas'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Ruta del archivo Excel')

    def normalizar_nombre_ruta(self, nombre_sucio):
        """Transforma CURICO 2, 3 -> CURICO 1"""
        nombre = str(nombre_sucio).upper().strip()
        
        # Diccionario de reglas de unificación
        # Si encuentra la CLAVE, devuelve el VALOR
        if "CURICO" in nombre: return "CURICO 1"
        if "TENO" in nombre: return "TENO 1"
        if "MONTAÑA" in nombre: return "LA MONTAÑA 1"
        if "MOLINA" in nombre: return "MOLINA 1" # Por si acaso aparecen más Molinas
        
        return nombre # Si no coincide con nada (ej: MORZA), lo devuelve tal cual

    def handle(self, *args, **kwargs):
        file_path = kwargs['excel_file']
        print(f"--- CARGA CON UNIFICACIÓN DE RUTAS ---")

        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.astype(str).str.upper().str.strip()
        except Exception as e:
            print(f"Error leyendo Excel: {e}")
            return

        df['FECHA'] = df['FECHA'].ffill()
        df['TURNO'] = df['TURNO'].ffill()

        user_sys, _ = User.objects.get_or_create(username='sistema_historico')
        chofer_gen, _ = Conductor.objects.get_or_create(rut='9999999-9', defaults={'nombre': 'CHOFER HISTÓRICO'})

        cache_vehiculos = {}
        cache_rutas = {}
        count = 0

        for index, row in df.iterrows():
            try:
                if pd.isna(row['RUTA']): continue

                # 1. NORMALIZACIÓN DE RUTA (Tu requerimiento #4)
                ruta_original = str(row['RUTA'])
                ruta_limpia = self.normalizar_nombre_ruta(ruta_original)

                # 2. PROCESAMIENTO ESTÁNDAR
                fecha_raw = row['FECHA']
                turno = str(row['TURNO']).upper()
                tipo = str(row['TIPO']).upper()
                pax = int(row['PAX']) if pd.notnull(row['PAX']) else 0
                
                try:
                    tarifa = int(float(str(row['TARIFA']).replace('$','').replace('.','').strip()))
                except:
                    tarifa = 0

                hora = time(8,0)
                if 'TURNO 2' in turno: hora = time(16,0)
                elif 'TURNO 3' in turno: hora = time(23,30)
                
                if not isinstance(fecha_raw, datetime): fecha_raw = pd.to_datetime(fecha_raw, dayfirst=True)
                fecha_final = timezone.make_aware(datetime.combine(fecha_raw.date(), hora))

                # Vehículo
                if 'MINIBUS' in tipo: mod, cap, pat = 'MINIBUS', 25, 'HIST-MINI'
                elif 'VAN' in tipo: mod, cap, pat = 'VAN', 17, 'HIST-VAN'
                else: mod, cap, pat = 'BUS', 42, 'HIST-BUS'

                if pat not in cache_vehiculos:
                    v, _ = Vehiculo.objects.get_or_create(patente=pat, defaults={'tipo':mod, 'capacidad':cap})
                    cache_vehiculos[pat] = v
                
                # Ruta (Usando el nombre LIMPIO)
                if ruta_limpia not in cache_rutas:
                    r, _ = Ruta.objects.get_or_create(nombre=ruta_limpia, defaults={'origen':'Planta', 'destino':ruta_limpia})
                    cache_rutas[ruta_limpia] = r
                
                RegistroSalida.objects.create(
                    fecha_registro=fecha_final,
                    registrado_por=user_sys,
                    ruta=cache_rutas[ruta_limpia],
                    vehiculo=cache_vehiculos[pat],
                    conductor=chofer_gen,
                    cantidad_pasajeros=pax,
                    valor_viaje=tarifa
                )
                count += 1
            except Exception as e:
                print(f"Error fila {index}: {e}")

        print(f"✅ LISTO. {count} registros cargados y rutas unificadas.")
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
        if pd.isna(valor_celda) or str(valor_celda).strip() == '':
            return None

        nombre = str(valor_celda).upper().strip()
        nombre = nombre.replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')

        if "CURICO" in nombre:
            if "1" in nombre: return "CURICO 1"
            if "2" in nombre: return "CURICO 2"
            if "3" in nombre: return "CURICO 3"
            return "CURICO 1"

        if "TENO" in nombre:
            if "CENTRO" in nombre: return "TENO 1"
            if "2" in nombre: return "TENO 2"
            return "TENO 1"

        if "MONTANA" in nombre or "MONTAÑA" in nombre:
            if "2" in nombre: return "LA MONTAÑA 2"
            return "LA MONTAÑA 1"

        if "MOLINA" in nombre: return "MOLINA"
        if "MORZA" in nombre: return "MORZA"
        if "RAUCO" in nombre: return "RAUCO"
        if "CHEPICA" in nombre: return "CHEPICA"

        return nombre

    def handle(self, *args, **kwargs):
        file_path = kwargs['excel_file']
        print("--- INICIANDO CARGA CON LIMPIEZA PROFUNDA ---")

        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.astype(str).str.upper().str.strip()
            print(f"Columnas encontradas: {list(df.columns)}")
        except Exception as e:
            print(f"❌ Error crítico leyendo el archivo: {e}")
            return

        df['FECHA'] = df['FECHA'].ffill()
        df['TURNO'] = df['TURNO'].ffill()

        user_sys, _ = User.objects.get_or_create(username='sistema_carga')
        chofer_gen, _ = Conductor.objects.get_or_create(
            rut='9999999-9',
            defaults={'nombre': 'CHOFER HISTÓRICO'}
        )

        cache_rutas = {}
        cache_vehiculos = {}

        registros_creados = 0
        errores = 0
        filas_fallidas = []

        for index, row in df.iterrows():
            try:
                ruta_raw = row.get('RUTA')
                ruta_final = self.normalizar_ruta(ruta_raw)

                if not ruta_final:
                    continue

                fecha_excel = row['FECHA']
                turno_str = str(row['TURNO']).upper()

                hora_viaje = time(8, 0)
                if 'TURNO 1' in turno_str:   hora_viaje = time(7, 30)
                elif 'TURNO 2' in turno_str: hora_viaje = time(16, 30)
                elif 'TURNO 3' in turno_str: hora_viaje = time(23, 30)

                if not isinstance(fecha_excel, datetime):
                    fecha_excel = pd.to_datetime(fecha_excel, dayfirst=True)

                fecha_completa = timezone.make_aware(
                    datetime.combine(fecha_excel.date(), hora_viaje)
                )

                try:
                    tarifa_str = str(row['TARIFA']).replace('$', '').replace('.', '').replace(' ', '')
                    tarifa = int(float(tarifa_str))
                except:
                    tarifa = 0

                try:
                    pax = int(row['PAX'])
                except:
                    pax = 0

                tipo_str = str(row['TIPO']).upper()
                if 'MINIBUS' in tipo_str:
                    modelo, cap, pat = 'MINIBUS', 25, 'HIST-MINI'
                elif 'VAN' in tipo_str:
                    modelo, cap, pat = 'VAN', 17, 'HIST-VAN'
                else:
                    modelo, cap, pat = 'BUS', 42, 'HIST-BUS'

                if pat not in cache_vehiculos:
                    v, _ = Vehiculo.objects.get_or_create(
                        patente=pat,
                        defaults={'tipo': modelo, 'capacidad': cap}
                    )
                    cache_vehiculos[pat] = v

                if ruta_final not in cache_rutas:
                    r, _ = Ruta.objects.get_or_create(
                        nombre=ruta_final,
                        defaults={'origen': 'Planta', 'destino': ruta_final}
                    )
                    cache_rutas[ruta_final] = r

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
                errores += 1
                filas_fallidas.append({
                    'fila_excel': index + 2,
                    'fecha'     : row.get('FECHA', '?'),
                    'turno'     : row.get('TURNO', '?'),
                    'ruta'      : row.get('RUTA', '?'),
                    'tipo'      : row.get('TIPO', '?'),
                    'tarifa'    : row.get('TARIFA', '?'),
                    'pax'       : row.get('PAX', '?'),
                    'motivo'    : str(e),
                })

        # ── Resumen final ──────────────────────────────────────────
        print(f"\n{'='*55}")
        print(f"✅ PROCESO TERMINADO")
        print(f"   Registros importados : {registros_creados}")
        print(f"   Filas con error      : {errores}")

        if filas_fallidas:
            print(f"\n{'─'*55}")
            print("⚠️  FILAS QUE REQUIEREN CARGA MANUAL:")
            print(f"{'─'*55}")
            for f in filas_fallidas:
                print(f"\n  Fila Excel #{f['fila_excel']}")
                print(f"    FECHA  : {f['fecha']}")
                print(f"    TURNO  : {f['turno']}")
                print(f"    RUTA   : {f['ruta']}")
                print(f"    TIPO   : {f['tipo']}")
                print(f"    TARIFA : {f['tarifa']}")
                print(f"    PAX    : {f['pax']}")
                print(f"    MOTIVO : {f['motivo']}")

        print(f"\n{'='*55}")
"""
LOAD — Quality checks y persistencia   *** PARCIALMENTE RESUELTO ***
=====================================================================

Dos responsabilidades, en este orden:

  1. CHEQUEAR: validar el dataset antes de publicarlo. Si algo crítico
     falla, cortamos: mejor no entregar nada que entregar un reporte roto.
  2. GUARDAR: escribir el CSV (para personas), el resumen JSON (para
     programas) y el log (para auditar).

Te dejamos resuelto el guardado del CSV y dos de los quality checks.
Faltan 4 TODOs (9 a 12), todos cortos.

Idempotencia: el CSV y el JSON van en modo "w", así que correr el pipeline
dos veces deja el mismo resultado. El log va en modo "a" porque un log ES
un historial: ahí sí queremos que crezca.
"""

import csv
import json
import logging
import os
from datetime import datetime

import config
from transform import COLUMNAS


# ======================================================================
# QUALITY CHECKS
# ======================================================================
def chequear_cantidad(filas, minimo=None):
    """¿Tenemos todas las filas que esperábamos?  [RESUELTO — de ejemplo]

    Fijate el patrón: devuelve una tupla (bool, mensaje). Todos los
    checks tienen que devolver lo mismo para que validar() los trate igual.
    """
    if minimo is None:
        minimo = config.MINIMO_FILAS_ESPERADAS
    ok = len(filas) >= minimo
    return ok, f"cantidad: {len(filas)} filas (mínimo esperado {minimo})"


def chequear_columnas(filas):
    """¿Todas las filas tienen exactamente las columnas del contrato?
    [RESUELTO — de ejemplo]
    """
    esperadas = set(COLUMNAS)
    for fila in filas:
        if set(fila.keys()) != esperadas:
            faltan = esperadas - set(fila.keys())
            return False, f"columnas: una fila no cumple el esquema (faltan {faltan})"
    return True, f"columnas: las {len(COLUMNAS)} del contrato en todas las filas"


def chequear_unicidad(filas):
    """¿Hay duplicados? La clave del dataset es (provincia, anio, destino).

    Debe devolver (bool, mensaje), igual que los checks de arriba.
    """
    # TODO 9 --------------------------------------------------------------
    claves = [(fila.get("provincia"), fila.get("anio"), fila.get("destino")) for fila in filas]
    unicas = set(claves)
    
    if len(claves) != len(unicas):
        return False, f"unicidad: se encontraron {len(claves) - len(unicas)} filas duplicadas para la misma clave (provincia, anio, destino)"
    
    return True, "unicidad: no hay filas duplicadas"
    # ---------------------------------------------------------------------


def chequear_rangos(filas):
    """¿Los valores son plausibles?

    Un valor negativo o mayor a config.VALOR_MAXIMO_RAZONABLE es
    sospechoso: no existen exportaciones negativas.
    """
    # TODO 10 -------------------------------------------------------------
    sospechosas = [
        f for f in filas 
        if f.get("valor_musd") is not None and (f["valor_musd"] < 0 or f["valor_musd"] > config.VALOR_MAXIMO_RAZONABLE)
    ]
    
    if sospechosas:
        return False, f"rangos: se encontraron {len(sospechosas)} filas con valores fuera de rango (negativos o mayores a {config.VALOR_MAXIMO_RAZONABLE})"
    
    return True, "rangos: todos los valores se encuentran en rangos plausibles"
    # ---------------------------------------------------------------------


def chequear_cobertura(filas):
    """Advertencia (no crítica): ¿cuántos nulos quedaron en las derivadas?
    [RESUELTO]
    """
    sin_variacion = sum(1 for f in filas if f["var_interanual_pct"] is None)
    sin_rubro = sum(1 for f in filas if f["rubro_principal"] is None)
    ok = sin_rubro == 0
    return ok, (f"cobertura: {sin_variacion} filas sin variación interanual "
                f"(esperable en el primer año), {sin_rubro} sin rubro")


def validar(filas):
    """Corre todos los checks.  [RESUELTO]

    Los CRÍTICOS cortan el pipeline lanzando una excepción ("fallar
    temprano y ruidosamente"). La cobertura solo deja una advertencia.

    Retorna una lista de dicts con el detalle, para el resumen JSON.
    """
    criticos = [
        chequear_cantidad(filas),
        chequear_columnas(filas),
        chequear_unicidad(filas),
        chequear_rangos(filas),
    ]

    detalle = []
    for ok, mensaje in criticos:
        detalle.append({"check": mensaje, "estado": "OK" if ok else "FALLO"})
        if ok:
            logging.info("  check OK    | %s", mensaje)
        else:
            logging.error("  check FALLO | %s", mensaje)
            raise ValueError(f"Quality check crítico falló -> {mensaje}")

    ok, mensaje = chequear_cobertura(filas)
    detalle.append({"check": mensaje, "estado": "OK" if ok else "AVISO"})
    if ok:
        logging.info("  check OK    | %s", mensaje)
    else:
        logging.warning("  check AVISO | %s", mensaje)

    return detalle


# ======================================================================
# PERSISTENCIA
# ======================================================================
def guardar_csv(filas, carpeta=None, nombre=None):
    """Escribe el dataset final. Modo 'w': cada corrida lo reemplaza.
    [RESUELTO — usalo de modelo para el resto]
    """
    carpeta = carpeta or config.DIR_PROCESSED
    nombre = nombre or config.ARCHIVO_SALIDA_CSV
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        escritor.writeheader()
        escritor.writerows(filas)

    logging.info("  CSV: %s (%s filas)", ruta, len(filas))
    return ruta


def construir_resumen(filas, detalle_checks):
    """Arma el resumen del proceso: metadatos + estadísticas descriptivas.

    Este JSON es la "ficha técnica" del dataset: quien lo reciba tiene que
    poder saber de dónde salió, cuándo y qué contiene, SIN abrir el CSV.

    CONTRATO: devolvé un dict que incluya al menos estas claves:

        dataset            (str)  nombre descriptivo
        fuente             (str)  de dónde salieron los datos
        unidad             (str)  "millones de dólares FOB"
        generado           (str)  fecha y hora de esta corrida
        filas              (int)
        columnas           (int)
        periodo            (dict) {"desde": anio_min, "hasta": anio_max}
        provincias         (list) ordenada
        valor_musd         (dict) {"minimo":…, "maximo":…, "promedio":…}
        quality_checks     (list) el detalle_checks que recibís
    """
    # TODO 11 -------------------------------------------------------------
    # 1. Extraemos los valores y los años para las estadísticas
    valores = [f["valor_musd"] for f in filas if f.get("valor_musd") is not None]
    anios = [f["anio"] for f in filas if f.get("anio") is not None]

    # 2. Cálculos estadísticos básicos protegidos contra listas vacías
    if valores:
        val_min = min(valores)
        val_max = max(valores)
        val_prom = round(sum(valores) / len(valores), 2)
    else:
        val_min, val_max, val_prom = 0, 0, 0.0

    if anios:
        anio_min = min(anios)
        anio_max = max(anios)
    else:
        anio_min, anio_max = None, None

    # 3. Armado del diccionario con el contrato requerido
    resumen = {
        "dataset": "Exportaciones provinciales por destino y rubro",
        "fuente": getattr(config, "URL_DESTINOS", "API oficial de exportaciones"),
        "unidad": "millones de dólares FOB",
        "generado": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "filas": len(filas),
        "columnas": len(COLUMNAS),
        "periodo": {
            "desde": anio_min,
            "hasta": anio_max
        },
        "provincias": sorted({f["provincia"] for f in filas if f.get("provincia")}),
        "valor_musd": {
            "minimo": val_min,
            "maximo": val_max,
            "promedio": val_prom
        },
        "quality_checks": detalle_checks
    }

    return resumen
    # ---------------------------------------------------------------------


def guardar_resumen(resumen, carpeta=None, nombre=None):
    """Escribe el resumen en JSON, legible por humanos y por programas.

    Acordate de los dos argumentos que vimos: ensure_ascii=False para que
    las tildes se guarden bien, e indent=2 para que sea legible.
    """
    # TODO 12a ------------------------------------------------------------
    if carpeta is None:
        carpeta = "data/processed"
    if nombre is None:
        nombre = "resumen.json"

    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    
    logging.info("  resumen guardado en %s", ruta)
    return ruta
    # ---------------------------------------------------------------------


def escribir_log_corrida(resumen, carpeta=None, nombre=None):
    """Agrega UNA línea al historial del pipeline.

    Modo "a" (append): nunca borra lo anterior. Cada corrida deja su rastro.
    Sugerencia de formato:

        2026-08-02 14:30 | OK | 1408 filas | 1993-2024
    """
    # TODO 12b ------------------------------------------------------------
    if carpeta is None:
        carpeta = "logs"
    if nombre is None:
        nombre = "pipeline.log"

    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)

    # Extraemos los datos del resumen para armar la línea de log
    fecha_generacion = resumen.get("generado", datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    # Revisamos si hubo algún fallo en los checks para definir el estado (OK / ERROR)
    checks = resumen.get("quality_checks", [])
    estado = "OK" if all(check[0] for check in checks if isinstance(check, (list, tuple)) and len(check) > 0) else "ERROR"
    
    cant_filas = resumen.get("filas", 0)
    
    periodo = resumen.get("periodo", {})
    desde = periodo.get("desde", "N/A")
    hasta = periodo.get("hasta", "N/A")
    
    linea = f"{fecha_generacion} | {estado} | {cant_filas} filas | {desde}-{hasta}\n"

    with open(ruta, "a", encoding="utf-8") as f:
        f.write(linea)
        
    logging.info("  log actualizado en %s", ruta)
    return ruta
    # ---------------------------------------------------------------------


def cargar(filas):
    """CONTRATO: recibe las filas finales; valida y persiste las 3 salidas.
    [RESUELTO]
    """
    logging.info("LOAD: validando")
    detalle = validar(filas)

    logging.info("LOAD: guardando")
    guardar_csv(filas)
    resumen = construir_resumen(filas, detalle)
    guardar_resumen(resumen)
    escribir_log_corrida(resumen)

    logging.info("LOAD OK")
    return resumen

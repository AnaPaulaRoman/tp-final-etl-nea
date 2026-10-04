# Pipeline ETL — Exportaciones Provinciales del NEA

## 1. Título y descripción
Este proyecto implementa un pipeline ETL (Extract, Transform, Load) automatizado en Python para procesar las series históricas de exportaciones de las provincias del Noreste Argentino (**Chaco, Corrientes, Formosa y Misiones**). Automatiza la extracción desde la API oficial, la limpieza y transformación de los datos, y aplica rigurosos controles de calidad (quality checks) antes de generar las salidas finales[cite: 1, 3].

---

## 2. Datos
- **Fuente**: API oficial de estadísticas de exportación (INDEC / series provinciales).
- **Contenido**: Datos históricos anuales (1993–2024) de exportaciones discriminados por provincia, destino geográfico y rubro comercial, transformados a una estructura tabular limpia de 13 columnas[cite: 2, 3].

---

## 3. Instalación
Para poner en marcha el proyecto en tu entorno local, cloná el repositorio y asegurate de tener instalado Python junto con las librerías estándar utilizadas en el proyecto.

---

## 4. Uso
El pipeline se ejecuta desde la terminal ubicándose en la carpeta raíz del proyecto con el siguiente comando:
```bash
python src/main.py

## 5. Salida
El proceso genera automáticamente los siguientes archivos de salida:
- **Dataset principal**: `data/processed/exportaciones_nea.csv` (CSV limpio con 1408 filas y 13 columnas)[cite: 2, 3].
- **Ficha técnica**: `data/processed/resumen.json` (Resumen en formato JSON con metadatos y estadísticas descriptivas).
- **Auditoría**: `logs/pipeline.log` (Registro histórico en modo *append* que acumula una línea por cada ejecución exitosa del pipeline)[cite: 3].

---

## 6. Estructura del proyecto
```text
tp-final-etl/
│
├── data/
│   └── processed/       # Archivos de salida (CSV y JSON limpios)
├── logs/
│   └── pipeline.log     # Historial de ejecuciones del pipeline
├── src/
│   ├── config.py        # Configuración centralizada de parámetros y rutas
│   ├── extract.py       # Lógica de descarga de la API
│   ├── transform.py     # Lógica de limpieza, tipado, cálculos y uniones
│   ├── load.py          # Quality checks y persistencia (CSV, JSON, log)
│   └── main.py          # Orquestador general del pipeline ETL
├── tests/               # Pruebas unitarias
└── README.md            # Documentación del proyecto

## 7. Autoría y Fecha
Autora: Ana Roman
Institución / Curso: Diplomatura en Data Analytics (UNNE) - Módulo 2
Fecha: 5 de Octubre de 2026

## 💡 Hallazgo en los datos
Al analizar el dataset procesado, se observa que China y Brasil se consolidan de forma sostenida entre los principales destinos comerciales de la región del NEA a lo largo de los años, destacándose un predominio del rubro de productos primarios en la estructura exportadora general[cite: 3].
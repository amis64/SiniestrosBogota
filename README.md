# Siniestros viales en Bogotá D.C. (2015-2020)

Descubrimiento de conocimiento evidente a partir de datos abiertos de Colombia.

Aplicación web desarrollada con Python, Flask y Bootstrap que presenta un análisis exploratorio de los siniestros viales ocurridos en Bogotá entre 2015 y 2020, mediante indicadores, comparaciones y visualizaciones interactivas, organizado en cuatro dimensiones de análisis.

Aplicación publicada: https://siniestrosbogota-stmd.onrender.com/

## Conjunto de datos

| Campo | Detalle |
|---|---|
| Nombre | Siniestros Viales Consolidados Bogotá D.C. |
| Tema | Seguridad vial y movilidad |
| Población estudiada | Siniestros viales ocurridos en Bogotá D.C., con las personas y los vehículos involucrados |
| Entidad que publica | Alcaldía Mayor de Bogotá D.C. (Datos Abiertos Bogotá) |
| Periodo | 1 de enero de 2015 a 31 de diciembre de 2020 |
| Licencia | CC BY 4.0 |
| URL | https://www.datos.gov.co/dataset/Siniestros-Viales-Consolidados-Bogot-D-C-/vftc-p83w/about_data |

El archivo original tiene cinco hojas que se relacionan por `CODIGO_ACCIDENTE`. Cada una está guardada como CSV en la carpeta `data/`.

| Hoja | Contenido | Registros |
|---|---|---|
| SINIESTROS | Fecha, hora, gravedad, clase, localidad, dirección y diseño del lugar | 196.152 |
| ACTOR_VIAL | Condición, estado, edad y sexo de cada persona involucrada | 422.416 |
| VEHICULOS | Clase, servicio, modalidad y si huyó del lugar | 371.605 |
| HIPOTESIS | Causa probable del siniestro | 233.819 |
| DICCIONARIO | Significado de cada código | 211 |

## Dimensiones de análisis

Cada dimensión es un tablero con su pregunta de análisis, descripción de variables, indicadores, visualizaciones, filtros interactivos, interpretaciones, conocimientos evidentes, una limitación y una decisión sustentada en los datos.

| # | Dimensión | Pregunta | Responsable | Rama |
|---|---|---|---|---|
| 1 | Poblacional | ¿Cómo está compuesta y distribuida la población analizada según sus principales características? | Integrante 1 | `feature/dimension-poblacional` |
| 2 | Territorial | ¿Cómo se distribuyen los siniestros entre las localidades? | Integrante 2 | `feature/dimension-territorial` |
| 3 | Temporal | ¿Cómo ha cambiado el comportamiento entre 2015 y 2020? | Integrante 3 | `feature/dimension-temporal` |
| 4 | Relacional y multivariada | ¿Qué relaciones hay al cruzar tres o más variables? | Integrante 4 | `feature/dimension-multivariada` |

## Equipo

| # | Integrante | Dimensión | Responsabilidad técnica |
|---|---|---|---|
| 1 | Amy Tatiana Gelves Espinosa | Poblacional | Administración del repositorio |
| 2 | David Santiago Arias Ramírez | Territorial | Configuración de Flask |
| 3 | John Sebastián Rodríguez Domínguez | Temporal | Publicación de la aplicación |
| 4 | Óscar Daniel Mancera Duarte | Relacional y multivariada | Informe técnico |

## Ejecución local

Requisitos: Python 3.14 (ver `.python-version`) y Git.

1. Clonar el repositorio y entrar a la carpeta:

   ```bash
   git clone https://github.com/amis64/SiniestrosBogota.git
   cd SiniestrosBogota
   ```

2. Crear y activar un entorno virtual:

   ```bash
   python -m venv venv
   ```

   - Windows (PowerShell): `venv\Scripts\Activate.ps1`
   - Linux o macOS: `source venv/bin/activate`

3. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Iniciar la aplicación:

   ```bash
   python app.py
   ```

5. Abrir en el navegador: http://127.0.0.1:5000

Los archivos CSV ya están incluidos en `data/`, por lo que no hace falta descargar nada más. La primera carga puede tardar unos segundos porque se leen y se preparan las tablas.

### Regenerar los CSV (opcional)

Solo si se quiere partir del Excel original: descargarlo desde datos.gov.co, copiarlo como `data/siniestros_viales_consolidados_bogota_dc.xlsx` y ejecutar:

```bash
python convetir.py
```

Genera un CSV por cada hoja del Excel. El Excel está excluido del repositorio en `.gitignore`.

## Estructura del repositorio

```
SiniestrosBogota/
├── app.py                  Aplicación Flask y registro de las dimensiones
├── datos.py                Carga y preparación de los datos (usado por las cuatro dimensiones)
├── convetir.py             Convierte el Excel original en un CSV por hoja
├── requirements.txt        Dependencias del proyecto
├── .python-version         Versión de Python
├── data/                   Archivos CSV del conjunto de datos
├── dimensiones/            Lógica de cada dimensión (un archivo por dimensión)
│   ├── poblacional.py
│   ├── territorial.py
│   ├── temporal.py
│   └── multivariada.py
├── templates/              Plantillas HTML (Jinja2 y Bootstrap)
│   ├── base.html           Diseño común y menú de navegación
│   ├── inicio.html
│   ├── poblacional.html
│   ├── territorial.html
│   ├── temporal.html
│   └── multivariada.html
└── static/
    └── estilos.css         Estilos de la aplicación
```

## Fuente de los datos

Alcaldía Mayor de Bogotá D.C. (Datos Abiertos Bogotá), publicado en el Portal Nacional de Datos Abiertos de Colombia con licencia CC BY 4.0.

# Gestion de Casos - Consultorio Juridico Universidad Icesi

Plataforma web desarrollada como proyecto academico para apoyar la gestion, reparto, seguimiento y trazabilidad de casos del Consultorio Juridico de la Universidad Icesi. El sistema propone una experiencia mas clara e intuitiva para reemplazar flujos operativos saturados, centralizando informacion, documentos, eventos, notificaciones y reportes.

## Funcionalidades principales

- Inicio de sesion unico con redireccion por roles y permisos.
- Paneles diferenciados para secretaria, estudiantes, asesores y beneficiarios.
- Gestion de casos con filtros por estado, estudiante, sala y tramite juridico.
- Reparto manual y automatico de casos.
- Reasignacion de casos con registro de trazabilidad.
- Bitacora del caso con entradas, documentos adjuntos y eventos relevantes.
- Resumen asistido de la bitacora del caso.
- Calendario por caso con eventos, disponibilidad y reuniones.
- Notificaciones internas y soporte para correo electronico.
- Reportes en Excel y estadisticas operativas.
- Seguimiento de casos retrasados y citas no atendidas.
- Pruebas unitarias y pruebas funcionales automatizadas con Selenium/Behave.

## Roles del sistema

- **Secretaria:** administra casos, reparte, reasigna, consulta reportes y revisa alertas operativas.
- **Asesor:** consulta casos asignados, bitacoras, documentos, calendario y notificaciones.
- **Estudiante:** gestiona casos asignados, registra eventos y consulta seguimiento.
- **Beneficiario:** consulta informacion y citas relacionadas con sus casos.

## Tecnologias

- Python
- Django
- PostgreSQL / SQLite para desarrollo local
- HTML, CSS y JavaScript
- WhiteNoise
- OpenPyXL
- Selenium, Behave y WebDriver Manager
- Microsoft Graph / Teams como integracion opcional

## Configuracion local

1. Clonar el repositorio.

```bash
git clone https://github.com/MekiahxAndres/Gestion-Casos-Consultorio-Juridico-Icesi.git
cd Gestion-Casos-Consultorio-Juridico-Icesi
```

2. Crear y activar un entorno virtual.

```bash
python -m venv venv
venv\Scripts\activate
```

3. Instalar dependencias.

```bash
pip install -r requirements.txt
```

4. Crear el archivo de variables de entorno.

```bash
copy .env.example .env
```

5. Aplicar migraciones y cargar datos demo.

```bash
python manage.py migrate
python manage.py seed_demo_data
```

6. Ejecutar el servidor.

```bash
python manage.py runserver
```

La aplicacion quedara disponible en `http://127.0.0.1:8000/`.

## Pruebas

Ejecutar pruebas unitarias y de integracion:

```bash
python manage.py test
```

Ejecutar pruebas funcionales con Behave:

```bash
behave test/selenium/features
```

## Nota de privacidad

Este repositorio fue preparado para portafolio. No incluye archivos `.env`, base de datos real, documentos cargados por usuarios, evidencias privadas, credenciales ni informacion sensible del cliente.

## Contexto academico

Proyecto desarrollado en el curso Proyecto Integrador I de la Universidad Icesi, trabajando con un cliente real y metodologia Scrum. Mi participacion se enfoco principalmente en el modulo de Gestion de Casos, flujos de reparto, bitacora, notificaciones, reportes, calendario, pruebas y ajustes de experiencia de usuario.

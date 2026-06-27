# Pruebas funcionales automatizadas - Consultorio Juridico ICESI

Este paquete contiene pruebas funcionales automatizadas con Selenium y Behave para el despliegue final:

`https://consultorio-juridico-icesi.up.railway.app`

## Estructura

```text
test/selenium/
  features/
    autenticacion.feature
    control_acceso.feature
    navegacion_paneles.feature
    tableros_reportes_notificaciones.feature
    environment.py
    steps/
      consultorio_steps.py
  pages/
    base_page.py
    login_page.py
    navigation_page.py
  screenshots/
    final_sprint/
  config.py
  test_cases.py
```

## Ejecucion rapida

Desde la raiz del proyecto:

```powershell
venv\Scripts\python.exe test\selenium\test_cases.py
```

Los escenarios publicos se ejecutan sin credenciales. Los escenarios autenticados requieren variables de entorno.

## Variables de entorno

```powershell
$env:CJ_BASE_URL="https://consultorio-juridico-icesi.up.railway.app"
$env:CJ_HEADLESS="true"

$env:CJ_SECRETARIA_DOC="documento_real"
$env:CJ_SECRETARIA_PASSWORD="clave_real"

$env:CJ_ASESOR_DOC="documento_real"
$env:CJ_ASESOR_PASSWORD="clave_real"

$env:CJ_ESTUDIANTE_DOC="documento_real"
$env:CJ_ESTUDIANTE_PASSWORD="clave_real"

$env:CJ_BENEFICIARIO_DOC="documento_real"
$env:CJ_BENEFICIARIO_PASSWORD="clave_real"
```

## Alcance

Las pruebas cubren flujos no destructivos:

- Carga del login del despliegue.
- Validacion de credenciales invalidas.
- Acceso a paneles por rol.
- Navegacion a gestion de casos, reporte de casos, tableros de casos retrasados y citas no atendidas.
- Centro de notificaciones.
- Control de acceso para beneficiario en rutas restringidas.

No se automatizan operaciones destructivas sobre produccion como crear, cerrar, reasignar o eliminar casos.

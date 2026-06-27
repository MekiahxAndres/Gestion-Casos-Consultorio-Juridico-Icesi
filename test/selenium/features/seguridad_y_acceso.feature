Feature: Seguridad de acceso y rutas restringidas
  Como sistema
  Quiero controlar sesiones, rutas protegidas y acceso administrativo
  Para evitar que usuarios no autorizados consulten informacion sensible

  Scenario: Usuario anonimo consulta recuperacion de contrasena
    Given que abro la aplicacion desplegada
    When abro directamente "/recuperar-contrasena/"
    Then debo ver alguno de estos textos
      | texto                 |
      | Recuperar contrasena  |
      | Correo                |
      | identificacion        |
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-024-recuperacion-contrasena"

  Scenario: Usuario anonimo conserva acceso al login institucional
    Given que abro la aplicacion desplegada
    Then debo ver el login institucional
    And debo ver alguno de estos textos
      | texto                |
      | Numero de documento  |
      | Ingresa tu contrasena|
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-025-login-institucional"

  Scenario: Login administrativo carga sin error de servidor
    Given que abro la aplicacion desplegada
    When abro directamente "/admin/"
    Then debo ver alguno de estos textos
      | texto          |
      | Django         |
      | Administracion |
      | Username       |
      | Usuario        |
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-026-admin-login"

  @requires_estudiante
  Scenario: Estudiante no debe ver accesos exclusivos de secretaria en su panel
    Given inicio sesion como "estudiante"
    Then no debo ver el texto "Reporte de Casos"
    And no debo ver el texto "Reparto Automatico Equitativo"
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-027-estudiante-sin-accesos-secretaria"

  @requires_beneficiario
  Scenario: Beneficiario no debe ver accesos operativos internos
    Given inicio sesion como "beneficiario"
    Then no debo ver el texto "Gestion de Casos"
    And no debo ver el texto "Reparto de Casos"
    And no debo ver el texto "Centro de Notificaciones"
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-028-beneficiario-sin-accesos-internos"

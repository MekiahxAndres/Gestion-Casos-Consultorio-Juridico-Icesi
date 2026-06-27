Feature: Funcionalidades principales de consulta
  Como usuario autorizado
  Quiero navegar a reportes, tableros y notificaciones
  Para validar las funcionalidades de seguimiento mas importantes del sistema

  @requires_secretaria
  Scenario: Secretaria consulta gestion y reporte de casos
    Given inicio sesion como "secretaria"
    When abro la ruta "/cases/secretaria/casos/"
    Then debo ver alguno de estos textos
      | texto            |
      | Gestion de Casos |
      | Gestión de Casos |
      | Casos            |
    And la pagina no debe mostrar error de servidor
    When abro la ruta "/cases/reporte/"
    Then debo ver el texto "Reporte de Casos"
    And debo ver alguno de estos textos
      | texto           |
      | Descargar Excel |
      | Total de casos  |
    And guardo evidencia con nombre "PF-007-secretaria-reporte-casos"

  @requires_secretaria
  Scenario: Secretaria consulta citas no atendidas
    Given inicio sesion como "secretaria"
    When abro la ruta "/cases/citas/no-atendidas/"
    Then debo ver alguno de estos textos
      | texto                            |
      | Tablero de citas no atendidas    |
      | Citas No Atendidas              |
    And debo ver estos textos
      | texto              |
      | No asistio         |
      | Pendiente vencida  |
    And guardo evidencia con nombre "PF-008-secretaria-citas-no-atendidas"

  @requires_asesor
  Scenario: Asesor consulta tablero de casos retrasados
    Given inicio sesion como "asesor"
    When abro la ruta "/cases/casos/retrasados/"
    Then debo ver alguno de estos textos
      | texto                         |
      | Tablero de casos retrasados   |
      | Casos Retrasados              |
    And debo ver estos textos
      | texto      |
      | Retrasados |
      | A tiempo   |
    And guardo evidencia con nombre "PF-009-asesor-casos-retrasados"

  @requires_asesor
  Scenario: Asesor consulta centro de notificaciones
    Given inicio sesion como "asesor"
    When abro la ruta "/notificaciones/"
    Then debo ver el texto "Centro de Notificaciones"
    And debo ver alguno de estos textos
      | texto                 |
      | Documentos subidos    |
      | Eventos importantes   |
      | Plazos                |
      | Inactividad           |
    And guardo evidencia con nombre "PF-010-asesor-notificaciones"

  @requires_estudiante
  Scenario: Estudiante consulta tableros asignados
    Given inicio sesion como "estudiante"
    When abro la ruta "/cases/casos/retrasados/"
    Then debo ver alguno de estos textos
      | texto                         |
      | Tablero de casos retrasados   |
      | Casos Retrasados              |
    When abro la ruta "/cases/citas/no-atendidas/"
    Then debo ver alguno de estos textos
      | texto                         |
      | Tablero de citas no atendidas |
      | Citas No Atendidas            |
    And guardo evidencia con nombre "PF-011-estudiante-tableros"

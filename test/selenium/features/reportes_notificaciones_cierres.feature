Feature: Reportes, notificaciones y cierres
  Como usuario autorizado
  Quiero consultar reportes, alertas y clasificaciones de cierre
  Para validar el seguimiento operativo del consultorio juridico

  @requires_secretaria
  Scenario: Secretaria consulta estadisticas del reporte de casos
    Given inicio sesion como "secretaria"
    When abro la ruta "/cases/reporte/"
    Then debo ver el texto "Reporte de Casos"
    And debo ver alguno de estos textos
      | texto              |
      | Beneficiarios      |
      | Sexo               |
      | Estrato            |
      | Total de casos     |
    And debo ver un acceso "Descargar Excel"
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-029-secretaria-reporte-estadisticas"

  @requires_secretaria
  Scenario: Secretaria consulta centro de notificaciones
    Given inicio sesion como "secretaria"
    When abro la ruta "/notificaciones/"
    Then debo ver el texto "Centro de Notificaciones"
    And debo ver alguno de estos textos
      | texto              |
      | Plazos             |
      | Inactividad        |
      | Eventos importantes|
      | Documentos subidos |
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-030-secretaria-notificaciones"

  @requires_secretaria
  Scenario: Secretaria visualiza clasificacion de casos cerrados en el panel
    Given inicio sesion como "secretaria"
    Then debo ver alguno de estos textos
      | texto            |
      | Cerrados         |
      | Tutela           |
      | Proceso judicial |
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-031-secretaria-casos-cerrados"

  @requires_asesor
  Scenario: Asesor consulta notificaciones de documentos y eventos
    Given inicio sesion como "asesor"
    When abro la ruta "/notificaciones/"
    Then debo ver el texto "Centro de Notificaciones"
    And debo ver alguno de estos textos
      | texto              |
      | Documentos subidos |
      | Eventos importantes|
      | Plazos             |
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-032-asesor-alertas-documentos-eventos"

Feature: Control de acceso por rol
  Como sistema
  Quiero bloquear rutas restringidas para roles no autorizados
  Para proteger informacion operativa de casos y citas

  @requires_beneficiario
  Scenario: Beneficiario no puede acceder al tablero de casos retrasados
    Given inicio sesion como "beneficiario"
    When abro directamente "/cases/casos/retrasados/"
    Then debo ver alguno de estos textos
      | texto         |
      | No autorizado |
      | Beneficiario  |
      | Panel         |
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-012-bloqueo-beneficiario-casos-retrasados"

  @requires_beneficiario
  Scenario: Beneficiario no puede acceder al reporte de citas no atendidas
    Given inicio sesion como "beneficiario"
    When abro directamente "/cases/citas/no-atendidas/"
    Then debo ver alguno de estos textos
      | texto         |
      | No autorizado |
      | Beneficiario  |
      | Panel         |
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-013-bloqueo-beneficiario-citas-no-atendidas"

Feature: Acceso a paneles por rol
  Como usuario autenticado
  Quiero ingresar a mi panel correspondiente
  Para validar que la redireccion por rol funcione en el despliegue final

  @requires_secretaria
  Scenario: Secretaria accede al panel principal
    Given inicio sesion como "secretaria"
    Then debo estar autenticado en el sistema
    And debo ver alguno de estos textos
      | texto                 |
      | Panel de Secretaria   |
      | Panel de Secretaría   |
    And debo ver estos textos
      | texto              |
      | Gestion de Casos   |
      | Reporte de Casos   |
      | Citas No Atendidas |
      | Notificaciones     |
    And guardo evidencia con nombre "PF-003-panel-secretaria"

  @requires_asesor
  Scenario: Asesor accede al panel de supervision
    Given inicio sesion como "asesor"
    Then debo estar autenticado en el sistema
    And debo ver alguno de estos textos
      | texto                 |
      | Panel de Supervision  |
      | Panel de Supervisión  |
    And debo ver estos textos
      | texto              |
      | Casos Retrasados   |
      | Citas No Atendidas |
      | Notificaciones     |
    And guardo evidencia con nombre "PF-004-panel-asesor"

  @requires_estudiante
  Scenario: Estudiante accede a su panel de caso asignado
    Given inicio sesion como "estudiante"
    Then debo estar autenticado en el sistema
    And debo ver el texto "Mi Caso Asignado"
    And debo ver estos textos
      | texto              |
      | Casos Retrasados   |
      | Citas No Atendidas |
      | Notificaciones     |
    And guardo evidencia con nombre "PF-005-panel-estudiante"

  @requires_beneficiario
  Scenario: Beneficiario accede a su panel
    Given inicio sesion como "beneficiario"
    Then debo estar autenticado en el sistema
    And debo ver alguno de estos textos
      | texto        |
      | Beneficiario |
      | Mis Citas    |
      | Panel        |
    And guardo evidencia con nombre "PF-006-panel-beneficiario"

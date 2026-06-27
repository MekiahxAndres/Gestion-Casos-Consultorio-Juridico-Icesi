Feature: Reparto, bitacora y calendario del caso
  Como usuarios autorizados
  Quiero validar flujos de seguimiento sin modificar datos sensibles
  Para comprobar que reparto, bitacora y calendario esten disponibles por rol

  @requires_secretaria
  Scenario: Secretaria consulta el tablero de reparto de casos
    Given inicio sesion como "secretaria"
    When abro la ruta "/cases/casos/distribuir/"
    Then debo ver el texto "Reparto de Casos"
    And debo ver alguno de estos textos
      | texto                         |
      | Reparto Automatico Equitativo |
      | Reparto Automatico            |
    And debo ver estos textos
      | texto              |
      | Sala               |
      | Tramite Juridico   |
      | Estudiante Asignado|
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-018-secretaria-reparto-listado"

  @requires_secretaria
  Scenario: Secretaria visualiza controles de asignacion y revision
    Given inicio sesion como "secretaria"
    When abro la ruta "/cases/casos/distribuir/"
    Then debo ver alguno de estos textos
      | texto             |
      | Asignar Caso      |
      | Enviar a Revision |
      | Completo          |
      | Incompleto        |
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-019-secretaria-controles-reparto"

  @requires_secretaria
  Scenario: Secretaria abre la bitacora desde el detalle del caso
    Given inicio sesion como "secretaria"
    When abro la ruta "/cases/secretaria/casos/"
    And selecciono el primer acceso que contiene "Ver"
    And selecciono el primer acceso que contiene "Bitacora"
    Then debo ver el texto "Bitacora del Caso"
    And debo ver alguno de estos textos
      | texto                 |
      | Registrar evento      |
      | Tipo de evento        |
      | Historial de Entradas |
    And guardo evidencia con nombre "PF-020-secretaria-bitacora-caso"

  @requires_estudiante
  Scenario: Estudiante consulta bitacora de su caso asignado
    Given inicio sesion como "estudiante"
    When selecciono el primer acceso que contiene "Bitacora"
    Then debo ver el texto "Bitacora del Caso"
    And debo ver alguno de estos textos
      | texto                 |
      | Registrar evento      |
      | Tipo de evento        |
      | Historial de Entradas |
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-021-estudiante-bitacora"

  @requires_estudiante
  Scenario: Estudiante abre calendario desde la bitacora
    Given inicio sesion como "estudiante"
    When selecciono el primer acceso que contiene "Bitacora"
    And selecciono el primer acceso que contiene "Calendario"
    Then debo ver alguno de estos textos
      | texto               |
      | Calendario del Caso |
      | Disponibilidad      |
      | Semana              |
      | Mes                 |
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-022-estudiante-calendario"

  @requires_asesor
  Scenario: Asesor accede a reparto y calendario operativo
    Given inicio sesion como "asesor"
    When abro la ruta "/cases/casos/distribuir/"
    Then debo ver alguno de estos textos
      | texto            |
      | Reparto de Casos |
      | Casos            |
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-023-asesor-reparto"

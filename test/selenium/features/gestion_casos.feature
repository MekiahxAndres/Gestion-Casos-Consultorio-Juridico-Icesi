Feature: Gestion de casos y filtros operativos
  Como secretaria
  Quiero consultar casos usando filtros y acciones visibles
  Para validar que la gestion principal permita ubicar casos sin errores

  @requires_secretaria
  Scenario: Secretaria visualiza filtros principales de gestion de casos
    Given inicio sesion como "secretaria"
    When abro la ruta "/cases/secretaria/casos/"
    Then debo ver alguno de estos textos
      | texto            |
      | Gestion de Casos |
      | Gestion          |
    And debo ver estos textos
      | texto            |
      | Estado           |
      | Estudiante       |
      | Sala             |
      | Tramite Juridico |
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-014-secretaria-filtros-gestion"

  @requires_secretaria
  Scenario: Secretaria filtra casos por texto y estado
    Given inicio sesion como "secretaria"
    When abro la ruta "/cases/secretaria/casos/"
    And escribo "000" en el buscador de casos
    And abro el filtro "Estado"
    Then debo ver alguno de estos textos
      | texto        |
      | Sin asignar  |
      | Autoasignado |
      | Asignado     |
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-015-secretaria-filtra-casos"

  @requires_secretaria
  Scenario: Secretaria abre el detalle de un caso desde gestion
    Given inicio sesion como "secretaria"
    When abro la ruta "/cases/secretaria/casos/"
    And selecciono el primer acceso que contiene "Ver"
    Then debo ver alguno de estos textos
      | texto              |
      | Estado del Proceso |
      | Documentos Adjuntos|
      | Detalle del Caso   |
    And debo ver alguno de estos textos
      | texto        |
      | Bitacora     |
      | Reasignar    |
      | Cambiar Estado |
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-016-secretaria-detalle-caso"

  @requires_secretaria
  Scenario: Secretaria identifica acciones segun estado del caso
    Given inicio sesion como "secretaria"
    When abro la ruta "/cases/secretaria/casos/"
    Then debo ver alguno de estos textos
      | texto       |
      | Asignar     |
      | Reasignar   |
      | Sin asignar |
    And no debo ver el texto "Traceback"
    And guardo evidencia con nombre "PF-017-secretaria-acciones-casos"

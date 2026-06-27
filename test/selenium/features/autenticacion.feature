Feature: Autenticacion del sistema desplegado
  Como equipo de pruebas
  Quiero validar el acceso inicial del sistema final
  Para comprobar que el despliegue responde y rechaza credenciales invalidas

  Scenario: El despliegue muestra el formulario de inicio de sesion
    Given que abro la aplicacion desplegada
    Then debo estar en el despliegue final
    And debo ver el login institucional
    And la pagina no debe mostrar error de servidor
    And guardo evidencia con nombre "PF-001-login-despliegue"

  Scenario: El sistema rechaza credenciales invalidas
    Given que abro la aplicacion desplegada
    When ingreso credenciales invalidas con documento "9999999999" y clave "clave_incorrecta"
    Then debo permanecer en el login con mensaje de error
    And guardo evidencia con nombre "PF-002-login-credenciales-invalidas"

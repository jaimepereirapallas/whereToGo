
# Nombre Proyecto: whereToGo

 
Breve descripción de la aplicación, y un listado de las funcionalidades implementadas hasta la primera iteración:
  
El objetivo de la aplicación es ofrecer a los usuarios una plataforma completa para la planificación de viajes. Permite buscar el clima actual y pronósticos futuros, recibir recomendaciones de destinos, visualizar lugares de interés, buscar y comparar vuelos y recibir alertas de cambios climáticos. Integra múltiples APIs para una experiencia de usuario completa y eficiente
  
  * Caso de uso 1 :
    **Login del usuario**: El usuario introduce dos palabras clave (el nombre de la cuenta y su contraseña) en los campos correspondientes. Una vez cubiertos, el usuario clica en el botón de “Iniciar sesión”.
 
  * Caso de uso 2 :
    **Búsqueda de Clima por Ubicación**: El usuario introduce una localización, a continuación mediante la llamada a dos APIs (para obtener las coordenadas del lugar y obtener el clima de dichas coordenadas geográficas) se le proporciona la temperatura actual, y varias gráficas mostrando información sobre las temperaturas, precipitaciones y propobabilidad de precipitaciones de la localización introducida.
* Caso de uso 3 :
    **Visualización de Lugares de Interés**: Una vez que el usuario introduce una localización en la funcionalidad anterior, podrá ver los lugarés de interés de dicha zona. Mediante la llamada a una API para obtener las coordenadas de la localización, lanzamos una petición a otra API para obtener los lugarés de interés de dicha zona.
* Caso de uso 4 :
    **Búsqueda de Ruta**: En la pantalla que el usuario visualiza los lugares de interés, tendrá la posibilidad de buscar una ruta para llegar a dicho destino, dónde se le pedirá que introduzca el origen desde el que parte. Mediante varias comparaciones (si compensa ir directamente en coche o si es mejor que se dirija en coche al aeropuerto más cercana y ahí coger un avión hacía el destino deseado), con eso le ofrecemos al usuario la ruta más óptima, que en caso de que tenga que obtener un billete de avión, también le damos la oportunidad de poder ver las ofertas de vuelos y que escoja la que más le interese.
* Caso de uso 5 :
    **Búsqueda de Vuelos**: Está funcionalidad podrá ser llamada desde la situación anterior o sino directamente una vez que el usuario realize la búsqueda de clima por ubicación. Para realizar la petición, se le pedirá al usuario que introduzca el origen del que parte, el número de pasajeros, el tipo de cabina y la fecha de salida. Se hará una petición a la API que en función de los criterior seleccionados nos mostrará los vuelos disponibles.
* Caso de uso 6 :
    **Comparación de Precios de Vuelos**: Es la funcionalidad posterior a la búsqueda de vuelos, dónde se muestra todos los vuelos disponibles mostrando su duración y el precio de dicho billete. 
* Caso de uso 7 :
    **Guardar Viajes Pendientes**: El usuario podrá guardar a elección las ofertas que se le proporcionaron, eso si, para poder realizar el guardado del viaje el usuario tendrá que estar logueado en el sistema, para posteriormente en su perfil acceder a las viajes que tenga guardados. 
* Caso de uso 8 :
    **Alertas Cambios Climáticos**: Para los viajes que el usuario tenga guardados, se hará una analisis de la temperatura de dicha zona durante las horas del día, y en caso de que de una hora a otra haya un cambio significativo con respecto a la temperatura, se mostrará una alerta. El objetivo de esta funcionalidad es detectar los picos/valles de la temperatura de nuestro viaje. 
* Caso de uso 9 :
    **Recomendación de Destinos**: El usuario indicará que tipo de clima desea (Nubes, Sol, Lluvia), y las fechas de salida y llegada. En función de los criterios seleccionados, mediante un analisis del histórico de datos climáticos podremos recomendar al usuario lugares que cumplan con sus requisitos (nota: Es una estimación basada en datos pasados, por lo que podría a ver diferencias con una situación futura)
 
Integrantes del grupo:
------------------
 
  * Yago Garcı́a Araújo <yago.garcia.araujo@udc.es>
  * Jaime Pereira Pallas <jaime.pereira@udc.es>
  * Jacobo Estévez Rouco <jacobo.erouco@udc.es> 
  
  
Cómo ejecutar:
--------------
 
Secuencia de comandos (docker) para descargar y lanzar la aplicación:
 
  1.- En la carpeta donde queremos alojar el proyecto: git clone git@github.com:GEI-PI-614G010492324/aplicacion-django-garcia_estevez_pereira.git
 
  2.- En VSCode pulsar en el menú de arriba: Archivo -> Abrir Carpeta... -> seleccionar la carpeta ../aplicacion-django-garcia_estevez_pereira.git
  
  3.- Cuando se hayan agregado los archivos de configuración, volver a escribir en el teclado la combinación "Ctrl+Alt+P" -> Pulsar en la opción "Dev Containers: Rebuild and Reopen in Container"

  4.- Una vez cargado el workspace, poner en el terminal "cd PIcommit/" -> (en caso de emplear la base de datos) "python manage.py makemigrations" -> "python3 manage.py migrate" -> (en caso de querer crear un superusuario) "python3 manage.py createsuperuser"
 
  5.- **La aplicación web se puede ejecutar** -> Poner en el terminal dentro de la carpeta "/workspaces/aplicacion-django-garcia_estevez_pereira/PIcommit": "python3 manage.py runserver", y acceder a la ip desplegada

  6.- Ejecutar los tests de la aplicación -> Poner en el terminal dentro de la carpeta "/workspaces/aplicacion-django-garcia_estevez_pereira/PIcommit": "python3 manage.py test", y ya se ejecutan los tests.


Problemas Conocidos:
--------------
* Puesto que se obtienen las coordenadas en función de un nombre, para algunos lugares nos proporcionan coordenadas que el resto de funcionalidades no procesan bien y no muestran resultados. Eso se debe a que el usuario solo pone el nombre y no otros parámetros como la provicia, país, etc... Sería una de las posibles mejoras futuras para asegurarnos que se obtiene las coordenadas precisas.
   * (Nota: Se añadieron dos coordenadas estáticas (Madrid y Coruña), para poder realizar los test y no saturar con peticiones a la API, además para estes lugares funciona perfectamente la aplicación).
* Por último, acotamos nuesta aplicación a nivel España, dónde incluimos la gran totalidad de los aeropuertos del país.


Cambios con respecto al anteproyecto:
--------------
* Se hicieron algunos ajustes a nivel estético en los templates de nuestra aplicación, como además de quitar el botón de Alertas Climáticas directamente en el perfil, y se puso dentro de Mis Viajes, para ver las alertas asociadas a cada uno de los viajes guardados por el usuario.
 

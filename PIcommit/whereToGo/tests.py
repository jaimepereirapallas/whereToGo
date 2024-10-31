from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse
import os
from django.utils import timezone
from django.contrib.auth import get_user
from whereToGo.views import *
from bs4 import BeautifulSoup

# Create your tests here.

class FunctionalityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.credential = {
            'username' : 'testuser',
            'password' : 'Testpassw0rd'
        }
        self.user = User.objects.create_user(username="testuser", password="Testpassw0rd")


    def test_created_user(self):
        self.assertIsInstance(self.user, User)
        self.assertEqual(self.user.username, "testuser")
        self.assertTrue(self.user.check_password("Testpassw0rd"))
        pass

    def test_user_login(self):
        url = reverse('login')
        self.assertFalse(get_user(self.client).is_authenticated)
        self.client.post(
            url, 
            self.credential,
            follow=True)
        
        self.assertTrue(get_user(self.client).is_authenticated)
        pass
    def test_searchbylocation(self):
        # Caso de éxito:
        url = reverse('searchbylocation')
        response = self.client.post(url, {'ubicacion': 'Coruña'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'whereToGo/searchbylocation.html')
        content = response.content.decode('utf-8')
        self.assertEqual(content.count('.png'), 3)
        self.assertContains(response, "Temperatura actual en Coruña")

        # Caso de error: 
        #Introducir ubicación sin empezar por letra mayúscula
        response0 = self.client.post(url, {'ubicacion': 'badlocation'}, follow=True)
        self.assertEqual(response0.status_code, 200)
        self.assertTemplateUsed(response0, 'whereToGo/home.html')
        self.assertContains(response0, "La ubicación debe comenzar con una letra mayúscula.")

        #Introducir ubicación con números
        response1 = self.client.post(url, {'ubicacion': '123Location'}, follow=True)
        self.assertEqual(response1.status_code, 200)
        self.assertTemplateUsed(response1, 'whereToGo/home.html')
        self.assertContains(response1, "La ubicación solo debe contener letras.")

        #Introducir ubicación de más de 15 caracteres
        response2 = self.client.post(url, {'ubicacion': 'UbicacionLargademásdecatorcecaracteres'}, follow=True)
        self.assertEqual(response2.status_code, 200)
        self.assertTemplateUsed(response2, 'whereToGo/home.html')
        self.assertContains(response2, "Ensure this value has at most 15 characters (it has 38).")
        response3 = self.client.post(url, {'ubicacion': 'Noexiste'}, follow=True)
        self.assertEqual(response3.status_code, 200)
        self.assertTemplateUsed(response3, 'whereToGo/home.html')
        self.assertContains(response3, "No se pudieron obtener las coordenadas")
        pass

    def test_searchbyweather(self):
        url = reverse('searchbyweather')

        #Caso de éxito
        data = {
            'clima': 'Sol',
            'fecha_llegada': '2024-07-05',
            'fecha_salida': '2024-07-10'
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        nombres_esperados = ['Zaragoza','Huesca','Sabadell','Badajoz','Logroño','Reus','Ibiza','Alicante','Málaga','Barcelona','Madrid']
        nombres_no_esperados=['Valencia', 'Sevilla', 'Granada', 'Bilbao', 'Cádiz', 'Girona', 'Santander', 'Salamanca', 'Valladolid', 'Tarragona']

        for nombre in nombres_esperados:
            self.assertContains(response, nombre)
        for nombre in nombres_no_esperados:
            self.assertNotContains(response, nombre)
        
        #Caso de error:
        #Indroducir una fecha anterior a la actual
        data = {
            'clima': 'Sol',
            'fecha_llegada': '2023-07-05',
            'fecha_salida': '2024-07-10'
        }
        response = self.client.post(url, data, follow=True)
        mensaje_advertencia = 'La fecha de salida o la fecha de llegada no puede ser anterior a la fecha actual.'
        self.assertContains(response, mensaje_advertencia)

        #Indroducir una fecha de llegada posterior a la de salida
        data = {
            'clima': 'Sol',
            'fecha_llegada': '2024-07-05',
            'fecha_salida': '2024-07-04'
        }
        response = self.client.post(url, data, follow=True)
        mensaje_advertencia = 'La fecha de llegada no puede ser posterior a la fecha de salida.'
        self.assertContains(response, mensaje_advertencia)

        #Indroducir parámetros que devuelvan ningún resultado
        data = {
            'clima': 'Nieve',
            'fecha_llegada': '2024-06-07',
            'fecha_salida': '2024-06-08'
        }
        response = self.client.post(url, data, follow=True)
        mensaje_advertencia = 'No se encontraron destinos que cumplan con los criterios seleccionados.'
        self.assertContains(response, mensaje_advertencia)

        pass
    def test_interestedplaces(self):
        #Caso de éxito
        url_location = reverse('searchbylocation')
        self.client.post(url_location, {'ubicacion': 'Coruña'},follow=True)
        url_interest = reverse('lugares_interes')
        response = self.client.get(url_interest, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'whereToGo/interestedplaces.html')
        self.assertContains(response, "Lugares más populares para visitar en Coruña")
        content = response.content.decode('utf-8')
        places_count = content.count('<div class="col-md-4">')
        self.assertEqual(places_count, 3)
        for i in range(3):
            self.assertIn('card-title', content)
            self.assertIn('card-text', content)
        self.assertGreater(content.count('<img src="'), 0, "Expected images in the response")

        #Caso de error no se contempla, porque ya hacemos las comprobaciones cuando se introduce para searchbylocation
        pass

    def test_searchflights(self):
        fecha_salida=timezone.now().date()
        url_location = reverse('searchbylocation')
        self.client.post(url_location, {'ubicacion': 'Coruña'},follow=True)
        url_interest = reverse('search_flights')
        data= {'origen': 'Madrid', 'pasajeros': '1', 'cabina': 'Economy', 'fecha_salida': fecha_salida}
        response=self.client.post(url_interest,data,follow=True)
        self.assertEqual(response.status_code, 200)

        

        #Caso de éxito
        soup = BeautifulSoup(response.content, 'html.parser')
        ofertas_html = soup.find_all(class_='flight-offer')
        self.assertTrue(ofertas_html)
        for oferta_html in ofertas_html:
            precio_element = oferta_html.find(class_='card-text')
            if precio_element:
                precio = precio_element.text.strip().split(':')[1].strip().split(' ')[0]
                # Comprueba que el precio sea un valor numérico positivo
                self.assertTrue(float(precio) >= 0)
        
        #Casos de error
        #Indroducir el destino con la primera en minúscula
        data= {'origen': 'madrid', 'pasajeros': '1', 'cabina': 'Economy', 'fecha_salida': fecha_salida}
        response=self.client.post(url_interest,data,follow=True)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        mensaje_error = soup.find(class_='alert alert-danger')

        if mensaje_error:
            
            mensaje= mensaje_error.text.strip()
            self.assertEqual("El origen debe empezar con una letra mayúscula y solo contener letras.",mensaje)


        #Indroducir una fecha no válida
        data= {'origen': 'Madrid', 'pasajeros': '1', 'cabina': 'Economy', 'fecha_salida': '2024/06/05'}
        response=self.client.post(url_interest,data,follow=True)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        mensaje_error = soup.find(class_='alert alert-danger')

        if mensaje_error:
            mensaje= mensaje_error.text.strip()
            self.assertEqual("Enter a valid date.",mensaje)
    
        #Indroducir una fecha anterior a la actual
        data= {'origen': 'Madrid', 'pasajeros': '1', 'cabina': 'Economy', 'fecha_salida': '06/05/2024'}

        response=self.client.post(url_interest,data,follow=True)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        mensaje_error = soup.find(class_='alert alert-danger')

        if mensaje_error:
            mensaje= mensaje_error.text.strip()
            self.assertEqual("La fecha de salida no puede ser anterior a la fecha actual.",mensaje)
        
        #Indroducir un número de pasajeros superior a 10 (max)
        data= {'origen': 'Madrid', 'pasajeros': '11', 'cabina': 'Economy', 'fecha_salida': fecha_salida}

        response=self.client.post(url_interest,data,follow=True)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        mensaje_error = soup.find(class_='alert alert-danger')

        if mensaje_error:
            mensaje= mensaje_error.text.strip()
            self.assertEqual("Ensure this value is less than or equal to 10.",mensaje)
            
        pass
    
    def test_findaroute(self):
        url_location = reverse('searchbylocation')
        self.client.post(url_location, {'ubicacion': 'Coruña'},follow=True)
        url_location = reverse('findaroute')
        response=self.client.post(url_location, {'origen': 'Madrid'},follow=True)
        self.assertEqual(response.status_code, 200)

        #Caso de éxito
        soup = BeautifulSoup(response.content, 'html.parser')

        route_details_right = soup.find('div', class_='route-details-right')

        distancia_element = None
        tiempo_element = None
        for p in route_details_right.find_all('p'):
            if 'Distancia al Aeropuerto: ' in p.text:
                distancia_element = p
            if 'Tiempo al Aeropuerto:' in p.text:
                tiempo_element = p.find('span', class_='green')
        
       
        distancia = distancia_element.text.split(':')[-1].strip().split()[0] 
        tiempo = tiempo_element.text.strip()


        distancia_esperada = '19.35'  
        tiempo_esperado = '00:23:13'  

        
        self.assertEqual(distancia, distancia_esperada)
        self.assertEqual(tiempo, tiempo_esperado)

        #Caso de error
        #Indroducir un origen no válido o que no tenga resultados
        response=self.client.post(url_location, {'origen': '1'},follow=True)
        soup = BeautifulSoup(response.content, 'html.parser')

        mensaje_error = soup.find('div', class_='info-box')
        if mensaje_error:
            mensaje= mensaje_error.text.strip()
            self.assertEqual("No hay resultados para mostrar.",mensaje)
        pass

    def test_savetrips(self):
        fecha_salida=timezone.now().date()
        url_location = reverse('searchbylocation')
        self.client.post(url_location, {'ubicacion': 'Coruña'},follow=True)
        url_interest = reverse('search_flights')
        data= {'origen': 'Madrid', 'pasajeros': '1', 'cabina': 'Economy', 'fecha_salida': fecha_salida}
        response_offer=self.client.post(url_interest,data,follow=True)
        self.assertEqual(response_offer.status_code, 200)


        #Caso de éxito guardar un viaje
        soup_offer = BeautifulSoup(response_offer.content, 'html.parser')
        flight_offer = soup_offer.find('div', class_='flight-offer')
        form = flight_offer.find('form', id='saveTripsForm')
        form_data = {input_tag['name']: input_tag['value'] for input_tag in form.find_all('input', type='hidden')}


        url_save=reverse('save_trips')
        url = reverse('login')
        self.client.post(url, self.credential,follow=True)
        response = self.client.post(url_save, form_data, follow=True)
        soup = BeautifulSoup(response.content, 'html.parser')
        login_modal = soup.find(id='successSave')

        self.assertIsNotNone(login_modal)
        self.assertIn('Viaje guardado correctamente.', login_modal.text)
        self.assertEqual(response.status_code, 200)

        url_view_trips=reverse('profile')
        response=self.client.get(url_view_trips)
        url_mytrip=reverse('mytrips')

        response=self.client.get(url_mytrip)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        card_title = soup.find('h3', class_='card-title')
        self.assertIsNotNone(card_title)
        self.assertTrue(card_title.text.strip())

        card_texts = soup.find_all('p', class_='card-text')
        self.assertGreater(len(card_texts), 0)
        for card_text in card_texts:
            self.assertTrue(card_text.text.strip())
        

        #Caso de error al guardar un viaje sin estar autenticado
        form = flight_offer.find('form', id='saveTripsForm')
        form_data = {input_tag['name']: input_tag['value'] for input_tag in form.find_all('input', type='hidden')}


        url_save=reverse('save_trips')
        response = self.client.post(url_save, form_data, follow=True)
        soup = BeautifulSoup(response.content, 'html.parser')
        login_modal = soup.find(id='loginModal')

        self.assertIsNotNone(login_modal)
        self.assertIn('Por favor, inicia sesión para guardar el viaje.', login_modal.text)
        self.assertEqual(response.status_code, 200)
        pass

    def test_climatealerts(self):
        fecha_salida=timezone.now().date()
        url_location = reverse('searchbylocation')
        self.client.post(url_location, {'ubicacion': 'Coruña'},follow=True)
        url_interest = reverse('search_flights')
        data= {'origen': 'Madrid', 'pasajeros': '1', 'cabina': 'Economy', 'fecha_salida': fecha_salida}
        response_offer=self.client.post(url_interest,data,follow=True)
        self.assertEqual(response_offer.status_code, 200)


        #Caso de éxito al cargar alertas
        soup_offer = BeautifulSoup(response_offer.content, 'html.parser')
        flight_offer = soup_offer.find('div', class_='flight-offer')
        form = flight_offer.find('form', id='saveTripsForm')
        form_data = {input_tag['name']: input_tag['value'] for input_tag in form.find_all('input', type='hidden')}


        url_save=reverse('save_trips')
        url = reverse('login')
        self.client.post(url, self.credential,follow=True)
        response = self.client.post(url_save, form_data, follow=True)
        soup = BeautifulSoup(response.content, 'html.parser')
        login_modal = soup.find(id='successSave')

        self.assertIsNotNone(login_modal)
        self.assertIn('Viaje guardado correctamente.', login_modal.text)
        self.assertEqual(response.status_code, 200)

        url_view_trips=reverse('profile')
        response=self.client.get(url_view_trips)
        url_mytrip=reverse('mytrips')

        response=self.client.get(url_mytrip)
        self.assertEqual(response.status_code, 200)
        url_alertas=reverse('climatealerts')
        data= {'destino': 'Madrid', 'fecha': fecha_salida}
        response_alertas=self.client.post(url_alertas,data)
        soup = BeautifulSoup(response_alertas.content, 'html.parser')
        alert_message = soup.find('div', class_='alert alert-danger').text.strip()
        self.assertEquals(alert_message,"Alerta meteorológica: ¡Se esperan cambios climáticos significativos para el día del vuelo!")
        table = soup.find('table', class_='table table-striped')
        rows = table.find_all('tr')
        assert len(rows) > 1

        #Caso de error
        #Acceder a las alertas climáticas de un viaje que ya no existe
        url_view_trips=reverse('profile')
        response=self.client.get(url_view_trips)
        url_mytrip=reverse('mytrips')
        response=self.client.get(url_mytrip)
        self.assertEqual(response.status_code, 200)
   
        soup = BeautifulSoup(response.content, 'html.parser')
        form = soup.find('form', {'action': reverse('del_trips')})
        trip_id_input = form.find('input', {'name': 'trip_id'})
        trip_id = trip_id_input['value']
        data={'trip_id':trip_id}
        url_deltrip=reverse('del_trips')
        response=self.client.post(url_deltrip,data)
        self.assertEqual(response.status_code, 302)
        
        response = self.client.get(url_mytrip)
        self.assertEqual(response.status_code, 200)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        form_alertas = soup.find('form', {'action': reverse('climatealerts')})
        self.assertIsNone(form_alertas)
        pass
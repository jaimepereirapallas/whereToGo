from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from whereToGo.forms import LoginForm, RegisterForm, SearchByLocationForm, FlightSearchForm
from django.contrib.auth.forms import UserCreationForm
import requests
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import matplotlib.pyplot as plt
import os
from PIcommit import settings
import matplotlib.dates as mdates
from .models import Trips
from geopy.distance import geodesic
from datetime import timedelta,datetime
import re
from django.utils import timezone
import urllib.parse




# Create your views here.

def home(request):
    
    if request.user.is_authenticated:
        username = request.user.username
        return render(request, 'whereToGo/home.html', {'username': username})
    else:
        return render(request, 'whereToGo/home.html')
    

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        if username is not None:
            request.session['username']=username
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Incorrect username or password.')
    
    loginForm = LoginForm() 
    return render(request, 'whereToGo/login.html', {'loginForm': loginForm})


def registerPage(request):
    signupForm=RegisterForm()
    return render(request, 'whereToGo/register.html', {'signup_form': signupForm})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                if username is not None:
                    request.session['username']=username
                login(request, user)
                return redirect('home')  
        else:
            error_message = "Hubo un problema en el formulario. Por favor, inténtalo de nuevo."
            return render(request, 'whereToGo/register.html', {'form': form, 'registerError': error_message})
    else:
        form = UserCreationForm()
    return render(request, 'whereToGo/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect(request.GET.get('next','/'))

def user_profile(request):
    user = request.user
    
    context = {
        'user': user,
    }
    return render(request, 'whereToGo/profile.html', context)

def obtener_coordenadas(direccion):
    # Se añaden dos casos estáticos para que no sature la API
    if direccion == "Coruña":
        return "-8.3959425,43.3709703"
    elif direccion == "Madrid":
        return "-3.70256,40.4165"
    else:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": direccion,
            "format": "json",
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "TuNombreDeApp/1.0 (tu.correo@example.com)"
        }
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()  
            data = response.json()
            if data:
                latitud = data[0]["lat"]
                longitud = data[0]["lon"]
                return f"{longitud},{latitud}"
            else:
                print("No se encontraron coordenadas para la dirección proporcionada.")
                return None
        except requests.exceptions.HTTPError as err:
            print(f"Error HTTP al obtener las coordenadas: {err}")
            return None
        except requests.exceptions.RequestException as err:
            print(f"Error al realizar la solicitud: {err}")
            return None
    
def generate_plot(latitud, longitud):
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitud, 
        "longitude": longitud, 
        "current": "temperature_2m",
        "hourly": ["temperature_2m", "precipitation_probability", "precipitation"]
    }

    responses = openmeteo.weather_api(url, params=params)

    if responses:
        response = responses[0]

        current = response.Current()

        current_temperature_2m = current.Variables(0).Value()


        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
        hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()



        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"
            )
        }
        hourly_data["temperature_2m"] = hourly_temperature_2m
        hourly_data["precipitation"] = hourly_precipitation
        hourly_data["precipitation_probability"] = hourly_precipitation_probability


        hourly_dataframe = pd.DataFrame(data=hourly_data)

        fig1, ax1 = plt.subplots(figsize=(6, 4))

        ax1.plot(hourly_dataframe['date'].values, hourly_dataframe['temperature_2m'].values, color='red')
        ax1.set_ylabel('Temperatura (°C)', color='red')
        plt.title('Gráfico de temperaturas')
        plt.grid(True)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%b'))

        image_path_temp= os.path.join(settings.MEDIA_ROOT, 'plottemperature.png')
        fig1.savefig(image_path_temp)
        plt.close(fig1) 

        fig2, ax2 = plt.subplots(figsize=(6, 4)) 

        ax2.bar(hourly_dataframe['date'].values, hourly_dataframe['precipitation'].values, color='lightblue')
        ax2.set_ylabel('Precipitación (mm)', color='blue')
        plt.title('Gráfico de precipitaciones')
        plt.grid(True)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d/%b'))
        
       
        image_path_precip= os.path.join(settings.MEDIA_ROOT, 'plotprecipitation.png')
        fig2.savefig(image_path_precip)
        plt.close(fig2) 


        current_day_data = hourly_dataframe[hourly_dataframe['date'].dt.date == pd.Timestamp.now().date()]
        
        fig3, ax3 = plt.subplots(figsize=(6, 4))

        ax3.plot(current_day_data['date'].values, current_day_data['temperature_2m'].values, color='lightcoral', label='Temperature (°C)')
        ax3.set_ylabel('Temperature (°C)', color='red')

        ax4 = ax3.twinx()
        ax4.bar(current_day_data['date'].values, current_day_data['precipitation_probability'].values, color='lightblue', alpha=0.5, width=0.05, label='Precipitation (mm)')
        ax4.set_ylabel('Precipitation (%)', color='blue')

        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        fig3.autofmt_xdate()
        fig3.tight_layout()

        lines, labels = ax3.get_legend_handles_labels()
        lines2, labels2 = ax4.get_legend_handles_labels()
        ax4.legend(lines + lines2, labels + labels2, loc='upper left')

        image_path_current_data = os.path.join(settings.MEDIA_ROOT, 'plotcurrentdata.png')
        fig3.savefig(image_path_current_data)
        plt.close(fig3)
        current_temperature_2m_form = "{:.0f}".format(round(float(current_temperature_2m)))
        return current_temperature_2m_form
    else:
        image_path_temp = os.path.join(settings.MEDIA_ROOT, 'plottemperature.png')
        image_path_precip = os.path.join(settings.MEDIA_ROOT, 'plotprecipitation.png')
        image_path_current_data = os.path.join(settings.MEDIA_ROOT, 'plotcurrentdata.png')

        
        if os.path.exists(image_path_temp):
            os.remove(image_path_temp)
        if os.path.exists(image_path_precip):
            os.remove(image_path_precip)
        if os.path.exists(image_path_current_data):
            os.remove(image_path_current_data)

def searchbylocation(request):
    if request.method == 'POST':
        form = SearchByLocationForm(request.POST)

        if form.is_valid():
            ubicacion = form.cleaned_data['ubicacion']
            coordenadas = obtener_coordenadas(ubicacion)  
            request.session['ubicacion'] = ubicacion

            if coordenadas:
                longitud, latitud = coordenadas.split(',')
                request.session['longitud_dest'] = longitud
                request.session['latitud_dest'] = latitud
                current_temp = generate_plot(latitud, longitud)

                return render(request, 'whereToGo/searchbylocation.html',{'current_temp': current_temp, 'ubicacion' : ubicacion})
            else:
                return render(request, 'whereToGo/home.html', {'form': form, 'error_message': 'No se pudieron obtener las coordenadas','ubicacion': ubicacion})
    else:
        form = SearchByLocationForm()
    return render(request, 'whereToGo/home.html',{'form': form})

def interestedplaces(request):
    ubicacion = request.session.get('ubicacion') 
    if not ubicacion:
        return redirect('searchbylocation')  
    longitud = request.session.get('longitud_dest') 
    latitud = request.session.get('latitud_dest') 

    if longitud and latitud: 
        params = {
            'lang': "en",
            'name': ubicacion,
            'radius': 5000,
            'lon': longitud,
            'lat': latitud,
            'apikey': '5ae2e3f221c38a28845f05b67e86be29ab8bebbafbd3821ec46bad25'
        }
        url = 'https://api.opentripmap.com/0.1/en/places/autosuggest'
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            places = []
            
            for place in data.get('features', [])[:3]:
                place_name = place['properties']['name']
                xid = place['properties']['xid']
                
                # Obtener detalles del lugar usando el xid
                detail_url = f'https://api.opentripmap.com/0.1/en/places/xid/{xid}'
                detail_response = requests.get(detail_url, params={'apikey': params['apikey']})
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    place_description = detail_data.get('wikipedia_extracts', {}).get('text', 'No description available')
                    place_image = detail_data.get('preview', {}).get('source', 'No image available')
                    
                    places.append({
                        'name': place_name,
                        'description': place_description,
                        'image': place_image,
                        'ubicacion': ubicacion
                    })
            
            return render(request, 'whereToGo/interestedplaces.html', {'places': places, 'ubicacion':ubicacion})
        else:
            return render(request, 'whereToGo/interestedplaces.html', {'error_message': 'Error al obtener datos de la API'})
    
    else:
        return render(request, 'whereToGo/interestedplaces.html', {'error_message': 'No se pudieron obtener las coordenadas'}) 
    
def search_flights(request):
    if request.method == 'POST':
        form = FlightSearchForm(request.POST)
        if form.is_valid():
            origen = form.cleaned_data.get('origen')
            pasajeros = form.cleaned_data.get('pasajeros')
            cabina = form.cleaned_data.get('cabina')
            fecha_salida = form.cleaned_data.get('fecha_salida')
            access_token = request.session.get('access_token')
            access_token = obtener_access_token(settings.apikey, settings.api_secret)

            codigo_aero_origen = request.session.get('codigo_aero_origen')
            codigo_aero_dest = request.session.get('codigo_aero_dest')
            if codigo_aero_origen is None:
                coordenadas_origen=obtener_coordenadas(origen)
                aeropuerto_origen = obtener_aeropuerto_mas_cercano(coordenadas_origen, settings.aeropuertos)
                codigo_aero_origen = settings.aeropuertos_iata.get(aeropuerto_origen)
            if codigo_aero_dest is None:
                long_dest= request.session.get('longitud_dest')
                lat_dest= request.session.get('latitud_dest')
                coordenadas_destino= f'{long_dest},{lat_dest}'
                aeropuerto_dest= obtener_aeropuerto_mas_cercano(coordenadas_destino, settings.aeropuertos)
                codigo_aero_dest = settings.aeropuertos_iata.get(aeropuerto_dest)
            
            ofertas_vuelos = consultar_ofertas_vuelos(codigo_aero_origen, codigo_aero_dest, fecha_salida, pasajeros, access_token)
            if ofertas_vuelos:
                request.session['ofertas']=ofertas_vuelos
                return render(request, 'whereToGo/flightsoffer.html', {'ofertas_vuelos': ofertas_vuelos['data']})
        else:
            return render(request, 'whereToGo/searchflights.html',{'form': form})
    else:
        form = FlightSearchForm()  
        
    return render(request, 'whereToGo/searchflights.html', {'form': form})

def obtener_access_token(apikey, api_secret):
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": apikey,
        "client_secret": api_secret
    }

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        access_token = response.json()["access_token"]
        return access_token
    except requests.exceptions.RequestException as e:
        print("Error al obtener el access token:", e)
        return None



def consultar_ofertas_vuelos(origen, destino, fecha_salida,pasajeros,access_token):
    if not access_token:
        print("No se pudo obtener el access token.")
        return None
        
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "originLocationCode": origen,
        "destinationLocationCode": destino,
        "departureDate": fecha_salida,
        "adults": pasajeros
    }

    try:
        response = requests.get(url, headers=headers,params=params)
        response.raise_for_status()
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        print("Error al hacer la solicitud:", e)
        return None

def obtener_aeropuerto_mas_cercano(origen, aeropuertos):
    coordenadas_origen = origen
    if coordenadas_origen is None:
        print("No se pudieron obtener las coordenadas del origen.")
        return None

    aeropuerto_mas_cercano = None
    distancia_minima = float('inf')

    for aeropuerto, coordenadas_aeropuerto in aeropuertos.items():
        distancia = geodesic(coordenadas_origen, coordenadas_aeropuerto).kilometers
        if distancia < distancia_minima:
            aeropuerto_mas_cercano = aeropuerto
            distancia_minima = distancia

    return aeropuerto_mas_cercano

def tiempo_a_segundos(tiempo_str):
    matches = re.search(r'PT(\d+)H(\d+)M', tiempo_str)
    horas = int(matches.group(1)) if matches.group(1) else 0
    minutos = int(matches.group(2)) if matches.group(2) else 0
    return horas * 3600 + minutos * 60
def sumar_tiempos(tiempo1, tiempo2):
    if isinstance(tiempo1, str):
        tiempo1_td = timedelta(hours=int(tiempo1.split(":")[0]), minutes=int(tiempo1.split(":")[1]), seconds=int(tiempo1.split(":")[2]))
    else:
        tiempo1_td = tiempo1
    
    if isinstance(tiempo2, str):
        tiempo2_td = timedelta(hours=int(tiempo2.split(":")[0]), minutes=int(tiempo2.split(":")[1]), seconds=int(tiempo2.split(":")[2]))
    else:
        tiempo2_td = tiempo2
    

    tiempo_total_td = tiempo1_td + tiempo2_td
    horas = int(tiempo_total_td.total_seconds() // 3600)
    minutos = int((tiempo_total_td.total_seconds() % 3600) // 60)
    segundos = int(tiempo_total_td.total_seconds() % 60)
    tiempo_total_str = "{:02d}:{:02d}:{:02d}".format(horas, minutos, segundos)
    
   
    return str(tiempo_total_str)

def obtener_tiempo_distancia(origen, destino):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    params = {
        "api_key": "5b3ce3597851110001cf6248587b6433455440eb8985363dc741d91f",
        "start": origen,
        "end": destino
    }
    headers = {
        "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8"
    }
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        distancia = data["features"][0]["properties"]["segments"][0]["distance"] / 1000  
        tiempo = data["features"][0]["properties"]["segments"][0]["duration"] / 60  
        return distancia, tiempo
    else:
        print("Error al obtener la ruta:", response.status_code)
        return None, None
    
def obtener_duracion_promedio_ofertas_vuelos(origen, destino, fecha_salida,pasajeros, access_token):
    ofertas_vuelos = consultar_ofertas_vuelos(origen, destino, fecha_salida,pasajeros, access_token)

    if ofertas_vuelos is None:
        return None

    duraciones = []
    for flight_offer in ofertas_vuelos["data"]:
        for itinerary in flight_offer["itineraries"]:
            for segment in itinerary["segments"]:
                duracion_str = segment["duration"]
                match_horas = re.search(r'(\d+)H', duracion_str)
                match_minutos = re.search(r'(\d+)M', duracion_str)

                if match_horas and match_minutos:
                    horas = int(match_horas.group(1))
                    minutos = int(match_minutos.group(1))
                    duracion_obj = timedelta(hours=horas, minutes=minutos)
                    duraciones.append(duracion_obj)

    if duraciones:
        duracion_total = sum(duraciones, timedelta())  
        duracion_promedio = duracion_total / len(duraciones)  
        return duracion_promedio
    else:
        print("No se encontraron duraciones válidas en las ofertas de vuelos.")
        return None
       
def get_image_url(query):
    access_key = 'bgtQKsWQuQ7u1EXE3usu3rNQrFj0ACR6OjXC6y4imoqV4TZZ42fBQqv6'
    url = 'https://api.pexels.com/v1/search'
    headers = {
        'Authorization': access_key
    }
    params = {
        'query': query,
        'per_page': 1
    }
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data['photos']:
            return data['photos'][0]['src']['medium']
        else:
            return 'No images found'
    else:
        return f"Error: {response.status_code}"

def findaroute(request):
    if request.method == 'POST':
        origen = request.POST.get('origen')
        destino = request.session.get('ubicacion')
        long_dest= request.session.get('longitud_dest')
        lat_dest= request.session.get('latitud_dest')
        coordenadas_destino= f'{long_dest},{lat_dest}'
        coordenadas_origen=obtener_coordenadas(origen)
        pasajeros = 1
        fecha_salida = datetime.now().date()
        fecha_salida = fecha_salida + timedelta(days=1)
    

        aeropuerto_origen = obtener_aeropuerto_mas_cercano(coordenadas_origen, settings.aeropuertos)
        aeropuerto_dest= obtener_aeropuerto_mas_cercano(coordenadas_destino, settings.aeropuertos)
        codigo_aero_origen = settings.aeropuertos_iata.get(aeropuerto_origen)
        request.session['codigo_aero_origen']=codigo_aero_origen
        codigo_aero_dest = settings.aeropuertos_iata.get(aeropuerto_dest)
        request.session['codigo_aero_dest']= codigo_aero_dest
            
        access_token = obtener_access_token(settings.apikey, settings.api_secret)
        request.session['access_token']=access_token
        
        aeropuertos = settings.aeropuertos 
        if codigo_aero_origen!=codigo_aero_dest:
            duracion_promedio = obtener_duracion_promedio_ofertas_vuelos(codigo_aero_origen, codigo_aero_dest, fecha_salida,pasajeros,access_token)
        else:
            duracion_promedio = timedelta(days=1, hours=0, minutes=0, seconds=0, microseconds=0)
        if coordenadas_origen is None or coordenadas_destino is None:
            return render(request, 'whereToGo/findaroute.html', {'mensaje': 'No se pudieron obtener las coordenadas del origen o destino.'})

        distancia_coche, tiempo = obtener_tiempo_distancia(coordenadas_origen, coordenadas_destino)
        if distancia_coche is not None:
            distancia_coche= round(distancia_coche, 2)


        aeropuerto_mas_cercano = obtener_aeropuerto_mas_cercano(coordenadas_origen, aeropuertos)
        coordenadas_aeropuerto = aeropuertos.get(aeropuerto_mas_cercano)
        distancia_aero, tiempo_aero = obtener_tiempo_distancia(coordenadas_origen, coordenadas_aeropuerto)
        if distancia_aero is not None:
            distancia_aero= round(distancia_aero, 2)
        

        if distancia_coche is None or tiempo is None:
            return render(request, 'whereToGo/findaroute.html', {'mensaje': 'No se pudo obtener la distancia y el tiempo.'})

        horas = int(tiempo / 60)
        minutos = int(tiempo % 60)
        segundos = int((tiempo % 1) * 60)
        tiempo_coche = "{:02d}:{:02d}:{:02d}".format(horas, minutos, segundos)

        if tiempo_coche is None or tiempo_aero is None:
            return render(request, 'whereToGo/findaroute.html', {'mensaje': 'No se pudo obtener los tiempos.'})

        horas = int(tiempo_aero / 60)
        minutos = int(tiempo_aero % 60)
        segundos = int((tiempo_aero % 1) * 60)
        tiempo_to_aero = "{:02d}:{:02d}:{:02d}".format(horas, minutos, segundos)
        tiempo_total = sumar_tiempos(duracion_promedio, tiempo_to_aero)

        imagen_ciudad = get_image_url(destino)

        if tiempo_coche > tiempo_total:
            resultado = {
            "ruta_mas_optima": "avion",
            "distancia_coche": distancia_aero,
            "tiempo_coche": tiempo_to_aero,
            "destino": codigo_aero_dest,
            "origen": codigo_aero_origen,
            "imagen":imagen_ciudad,
            "destino_global": destino
            }   
        else:
            resultado = {
            "ruta_mas_optima": "coche",
            "distancia_total": distancia_coche,
            "tiempo_coche": tiempo_coche,
            "imagen":imagen_ciudad,
            "destino_global": destino
            }   

        return render(request, 'whereToGo/findaroute.html', {'resultado': resultado})

    return render(request, 'whereToGo/findaroute.html')
    
def mytrips(request):
    user = request.user
    trips = Trips.objects.filter(user=user) 
    iata_to_city = {code: city for city, code in settings.aeropuertos_iata.items()}
    
    for trip in trips:
        
        city_dest = iata_to_city.get(trip.destination)
        city_orig = iata_to_city.get(trip.origin)
        
        if city_dest:
            if city_dest == "La Coruña":
                city_dest = "Coruña"
            
            
            trip.image = get_image_url(city_dest.replace(" ", "%20"))
            trip.destination = city_dest
            trip.origin = city_orig
            
            
        else:
           
            trip.image = get_image_url(trip.destination)
    
    return render(request, 'whereToGo/mytrips.html', {'trips': trips})

def obtener_datos_climaticos(latitude, longitude, start_date, end_date):
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["temperature_2m_mean", "precipitation_sum", "snowfall_sum"]
    }

    responses = openmeteo.weather_api(url="https://archive-api.open-meteo.com/v1/archive", params=params)
    if responses:
        response = responses[0]
        daily = response.Daily()
        daily_temperature_2m_mean = daily.Variables(0).ValuesAsNumpy()
        daily_precipitation_sum = daily.Variables(1).ValuesAsNumpy()
        daily_snowfall_sum = daily.Variables(2).ValuesAsNumpy()

        daily_data = {"date": pd.date_range(
            start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
            end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = daily.Interval()),
            inclusive = "left"
        )}

        temperature_mean = sum(daily_temperature_2m_mean) / len(daily_temperature_2m_mean)
        precipitation_mean = sum(daily_precipitation_sum) / len(daily_precipitation_sum)
        snowfall_mean = sum(daily_snowfall_sum) / len(daily_snowfall_sum)

        daily_data["temperature_mean"]=temperature_mean
        daily_data["precipitation_mean"]=precipitation_mean
        daily_data["snowfall_mean"]=snowfall_mean

        return pd.DataFrame(data=daily_data)
    else:
        return None


def verificar_condicion_clima(lluvia, nieve, soleado, sun, rain, snow):
    if lluvia and any(rain > 5):
        return True
    elif nieve and any(snow > 0.5):
        return True
    elif soleado and any(sun > 23):
        return True
    else:
        return False
    
def obtener_prediccion_climatica(latitud, longitud, fecha):
    cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    fecha_str = fecha.strftime("%Y-%m-%d")
    fecha_pasado = '2023' + fecha_str[4:]
    
    url = "http://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitud,
        "longitude": longitud,
        "start_date": fecha_pasado,
        "end_date": fecha_pasado,
        "hourly": ["temperature_2m", "precipitation", "cloud_cover"]
    }
    
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(1).ValuesAsNumpy()
    hourly_cloud_cover = hourly.Variables(2).ValuesAsNumpy()
    
    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}
    hourly_data["temperature_2m"]= hourly_temperature_2m
    hourly_data["precipitation"]= hourly_precipitation
    hourly_data["cloud_cover"]= hourly_cloud_cover

    hourly_dataframe = pd.DataFrame(data = hourly_data)

    
    return hourly_dataframe

def verificar_cambios_climaticos(weather_data):
    cambios_climaticos=False
    weather_data_list=[]
    for i in range(1,len(weather_data['date'])):
                    temperature_diff = abs(weather_data['temperature_2m'][i] - weather_data['temperature_2m'][i-1])
                    THRESHOLD_TEMPERATURE_DIFF = 0.5
                    if temperature_diff > THRESHOLD_TEMPERATURE_DIFF:
                        weather_data_list.append({
                            'date': weather_data['date'][i],
                            'temperature_2m': weather_data['temperature_2m'][i],
                            'precipitation': weather_data['precipitation'][i],
                            'cloud_cover': weather_data['cloud_cover'][i]
                        })
    if weather_data_list: cambios_climaticos=True


    return weather_data_list,cambios_climaticos

def searchbyweather(request):
    if request.method == 'POST':
        clima = request.POST.get('clima')
        fecha_llegada = request.POST.get('fecha_llegada')
        fecha_salida = request.POST.get('fecha_salida')
        if fecha_llegada and fecha_salida:
            fecha_actual = timezone.now().date()
            fecha_llegada_obj = timezone.datetime.strptime(fecha_llegada, '%Y-%m-%d').date()
            fecha_salida_obj = timezone.datetime.strptime(fecha_salida, '%Y-%m-%d').date()

            if fecha_llegada_obj < fecha_actual or fecha_salida_obj < fecha_actual:
                messages.error(request, "La fecha de salida o la fecha de llegada no puede ser anterior a la fecha actual.")
                return render(request, 'whereToGo/home.html')
            elif fecha_llegada_obj > fecha_salida_obj:
                messages.error(request, "La fecha de llegada no puede ser posterior a la fecha de salida.")
                return render(request, 'whereToGo/home.html')

            fecha_llegada = '2023' + fecha_llegada[4:]
            fecha_salida = '2023' + fecha_salida[4:]

        destinos = []
        for lugar in settings.lugares:
            data_frame = obtener_datos_climaticos(lugar['lat'], lugar['lon'], fecha_llegada, fecha_salida)
            if data_frame is not None:
                clima_cumplido = verificar_condicion_clima(
                    clima == 'Lluvia',
                    clima == 'Nieve',
                    clima == 'Sol',
                    data_frame["temperature_mean"],
                    data_frame["precipitation_mean"],
                    data_frame["snowfall_mean"]
                )
                if clima_cumplido:
                    nombre_codificado = urllib.parse.quote(lugar['nombre'], safe='')
                    imagen_nombre = nombre_codificado.lower().replace(" ", "_") + ".jpg"
                    imagen_url = os.path.join(settings.MEDIA_URL, imagen_nombre)
                    destino = {"nombre": lugar['nombre'], "imagen_url": imagen_url}
                    destinos.append(destino)
                

    
        return render(request, 'whereToGo/searchbyweather.html', {'destinos': destinos})

    return render(request, 'whereToGo/searchbyweather.html')

def climatealerts(request):
    if request.method=='POST':
        fecha= request.POST.get('fecha')
        destino=request.POST.get('destino')
        if fecha:
            fecha_llegada = datetime.strptime(fecha, '%Y-%m-%d')
        else:
            fecha_llegada = datetime.now().date()

        alertas_climaticas = {}
        weather_data_list=[]
        coordenadas=settings.aeropuertos.get(destino)
        latitud, longitud = map(float, coordenadas.split(","))
            
        prediccion_climatica = obtener_prediccion_climatica(latitud, longitud, fecha_llegada)
        
        if prediccion_climatica is not None:
            weather_data_list,cambios_climaticos=verificar_cambios_climaticos(prediccion_climatica)

            if cambios_climaticos:
                alertas_climaticas[destino] = "Se ha detectado un pico en las condiciones meteorológicas"
            else:
                alertas_climaticas[destino] = "Condiciones meteorológicas favorables"
                
            
        return render(request, 'whereToGo/climatealerts.html', {
            'alertas_climaticas': alertas_climaticas, 
            'fecha': fecha_llegada, 
            'weather_data_list': weather_data_list, 
            'cambios_climaticos': cambios_climaticos
            })
    return render (request,'whereToGo/mytrips.html')

def save_trip(request):
    if request.method == 'POST':
        origen = request.POST.get('origen')
        destino = request.POST.get('destino')
        fecha_salida = request.POST.get('fecha_salida')
        fecha_llegada = request.POST.get('fecha_llegada')
        tipo_vuelo = request.POST.get('tipo_vuelo')
        username = request.session.get('username')
        ofertas = request.session.get('ofertas')
        coordenadas=settings.aeropuertos_iata_coor.get(destino)
        lat, long = map(float, coordenadas.split(","))

        

        if username is not None:
            user = User.objects.get(username=username)
            trip = Trips(user=user, origin=origen, destination=destino, takeoff=fecha_salida, arrival=fecha_llegada, escalas=tipo_vuelo,latitude=lat,longitude=long)
            trip.save()
            return render(request, 'whereToGo/flightsoffer.html', {'username': username, 'message_succ': "Viaje guardado", 'ofertas_vuelos': ofertas['data']})
        else:
            return render(request, 'whereToGo/flightsoffer.html', {'message_fail': "Para poder guardar un viaje debes loguearte", 'ofertas_vuelos': ofertas['data']})

    return render(request, 'whereToGo/flightsoffer.html', {'ofertas_vuelos': ofertas['data']})

def del_trip(request):
    if request.method == 'POST':
        trip_id = request.POST.get('trip_id')
        trip = Trips.objects.get(id=trip_id)
        trip.delete()
        return redirect('mytrips')
    return render(request, 'whereToGo/mytrips.html')
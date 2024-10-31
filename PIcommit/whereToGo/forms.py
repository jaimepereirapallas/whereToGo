from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, ButtonHolder

from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
import re
from django.utils import timezone


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username',
            'password',
            ButtonHolder(
                 Submit('login', 'Login', css_class='btn-primary')
            )
        )

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)
    password_repeat = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password1']

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("El nombre de usuario ya está en uso.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 != password2:
            raise ValidationError("Las contraseñas no coinciden.")
        return cleaned_data
    

class SearchByLocationForm(forms.Form):
    ubicacion = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Introduce una ubicación...'
        })
    )

    def clean_ubicacion(self):
        ubicacion = self.cleaned_data.get('ubicacion')

        # Verificar que solo contenga letras
        if not re.match(r'^[A-Za-zÁÉÍÓÚÑáéíóúñ]*$', ubicacion):
            raise forms.ValidationError('La ubicación solo debe contener letras.')

        # Verificar que no tenga más de 15 caracteres
        if len(ubicacion) > 15:
            raise forms.ValidationError('La ubicación no puede tener más de 15 caracteres.')

        # Verificar que comienza con una letra mayúscula
        if not re.match(r'^[A-ZÁÉÍÓÚÑ]', ubicacion):
            raise forms.ValidationError('La ubicación debe comenzar con una letra mayúscula.')

        return ubicacion

class FlightSearchForm(forms.Form):
    origen = forms.CharField( max_length=100, required=True,widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Introduce el origen...'
        }))
    pasajeros = forms.IntegerField(min_value=1, max_value=10, required=True,widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Introduce el número de pasajeros...'
        }))
    fecha_salida = forms.DateField(label='Fecha de Salida', required=True, widget=forms.DateInput(attrs={'type': 'date'}))

    def clean_origen(self):
        origen = self.cleaned_data['origen']
        if not re.match(r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]*$', origen):
            raise forms.ValidationError('El origen debe empezar con una letra mayúscula y solo contener letras.')
        return origen

    def clean_fecha_salida(self):
        fecha_salida = self.cleaned_data['fecha_salida']
        if fecha_salida < timezone.now().date():
            raise forms.ValidationError('La fecha de salida no puede ser anterior a la fecha actual.')
        return fecha_salida
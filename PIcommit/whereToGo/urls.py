
from django.urls import path
from . import views

urlpatterns = [
      path("", views.home, name="home"),
      path("register/", views.register, name="register"),
      path("profile/",views.user_profile, name="profile"),
      path('logout/', views.logout_view, name='logout_view'),
      path("searchbylocation/", views.searchbylocation, name="searchbylocation"),
      path("login/",views.user_login, name="login"),
      path("interestedplaces/",views.interestedplaces, name="lugares_interes"),
      path("searchflights/",views.search_flights, name="search_flights"),
      path("mytrips/",views.mytrips,name="mytrips"),
      path("findaroute/",views.findaroute, name="findaroute"),
      path("searchbyweather/",views.searchbyweather,name="searchbyweather"),
      path("savetrips/", views.save_trip, name="save_trips"),
      path("deltrip/", views.del_trip, name="del_trips"),
      path("climatealerts/",views.climatealerts, name="climatealerts")
]

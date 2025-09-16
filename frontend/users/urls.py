from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home_view, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('api-config/', views.api_config, name='api_config'),
    path('movie/<int:movie_id>/', views.get_movie_details, name='movie_details'),
    path('rate-movie/', views.rate_movie, name='rate_movie'),
    path('profile-data/', views.get_profile_data, name='profile_data'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('change-password/', views.change_password, name='change_password'),
]
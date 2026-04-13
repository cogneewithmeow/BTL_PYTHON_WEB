from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name = 'home'),
    path('register/', views.register, name = 'register'),
    path('login/', views.loginPage, name = 'login'),
    path('logout/', views.logoutPage, name = 'logout'),
    path('search/', views.search, name = 'search'),
    path('category/', views.category, name = 'category'),
    path('cart/', views.cart, name = 'cart'),
    path('detail/', views.detail, name = 'detail'),
    path('profile/', views.profile, name = 'profile'),
    path('checkout/', views.checkout, name = 'checkout'),
    path('success/', views.success, name = 'success'),
    path('update_item/', views.updateItem, name = 'update_item'),
    path('update_profile/', views.update_profile, name = 'update_profile'),
]
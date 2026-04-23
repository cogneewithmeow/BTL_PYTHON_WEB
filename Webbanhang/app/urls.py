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
    path('review/add/', views.add_review, name='add_review'),
    path('review/edit/<int:product_id>/', views.edit_review, name='edit_review'),
    path('review/helpful/<int:review_id>/', views.toggle_helpful_review, name='toggle_helpful_review'),
    path('profile/', views.profile, name = 'profile'),
    path('checkout/', views.checkout, name = 'checkout'),
    path('success/', views.success, name = 'success'),
    path('update_item/', views.updateItem, name = 'update_item'),
    path('update_profile/', views.update_profile, name = 'update_profile'),
    path('api/chat/', views.api_chat, name='api_chat'),
]
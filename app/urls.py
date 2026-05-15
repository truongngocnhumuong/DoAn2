from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('update_item/', views.updateItem, name='update_item'),
    path('register/', views.register, name='register'),
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutPage, name='logout'),
    path('search/', views.search, name='search'),
    path('category/', views.category, name='category'),
    path('detail/', views.detail, name='detail'),
    path('contact/', views.contact, name='contact'),
    path('process_order/', views.process_order, name='process_order'),
    path('statistics/', views.statistics, name='statistics'),
    # CT2: Lịch sử đơn hàng
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order-status/<int:pk>/', views.update_order_status, name='update_order_status'),
    # CT3: Trang cá nhân
    path('profile/', views.profile, name='profile'),
]
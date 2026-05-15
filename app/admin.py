from django.contrib import admin
from .models import Category, Contact, Product, Order, OrderItem, ShippingAddress, UserProfile


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'in_stock']
    list_editable = ['stock']
    list_filter = ['category']
    search_fields = ['name']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'date_order', 'complete', 'status', 'get_cart_total']
    list_editable = ['status']
    list_filter = ['status', 'complete']
    search_fields = ['customer__username', 'transaction_id']
    readonly_fields = ['transaction_id', 'date_order']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'order', 'quantity']


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['customer', 'order', 'address', 'city', 'mobile']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_sub']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['fullname', 'email', 'phone', 'date_created', 'is_read']
    list_editable = ['is_read']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'date_updated']
    search_fields = ['user__username', 'phone']
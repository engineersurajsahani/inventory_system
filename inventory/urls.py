from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('products/', views.product_list, name='products'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:pk>/', views.delete_product, name='delete_product'),
    
    path('bills/', views.bills, name='bills'),
    path('bills/generate/', views.generate_bill, name='generate_bill'),
    path('bills/<int:bill_id>/', views.view_bill, name='view_bill'),
    path('bills/<int:bill_id>/download/', views.download_bill, name='download_bill'),
    
    path('reports/', views.reports, name='reports'),
]
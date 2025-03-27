from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Product, Transaction, Bill, BillItem

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'validate'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'validate'}))

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'quantity', 'price', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'validate'}),
            'quantity': forms.NumberInput(attrs={'class': 'validate'}),
            'price': forms.NumberInput(attrs={'class': 'validate'}),
            'description': forms.Textarea(attrs={'class': 'materialize-textarea'}),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['product', 'transaction_type', 'quantity', 'price', 'notes']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'validate'}),
            'price': forms.NumberInput(attrs={'class': 'validate'}),
            'notes': forms.Textarea(attrs={'class': 'materialize-textarea'}),
        }

class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['customer_name', 'customer_contact']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'validate'}),
            'customer_contact': forms.TextInput(attrs={'class': 'validate'}),
        }

class BillItemForm(forms.ModelForm):
    class Meta:
        model = BillItem
        fields = ['product', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'validate'}),
        }
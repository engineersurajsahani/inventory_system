import io
from pyexpat.errors import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import matplotlib.pyplot as plt
from .models import Product, Transaction, Bill, BillItem
from .forms import LoginForm, ProductForm, TransactionForm, BillForm, BillItemForm
from .utils import generate_pdf_report
import base64
import io
from datetime import timedelta

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'inventory/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    # Get product counts
    total_products = Product.objects.count()
    low_stock = Product.objects.filter(quantity__lt=10).count()
    
    # Get recent transactions
    recent_transactions = Transaction.objects.order_by('-transaction_date')[:5]
    
    # Get sales data for chart
    today = timezone.now().date()
    last_week = today - timedelta(days=7)
    
    sales_data = Transaction.objects.filter(
        transaction_type='SALE',
        transaction_date__gte=last_week
    ).values('transaction_date__date').annotate(
        total_sales=Sum('total_amount')
    ).order_by('transaction_date__date')
    
    # Prepare chart data
    dates = []
    amounts = []
    
    # Fill in dates for the entire week, even if no sales
    for i in range(7):
        current_date = last_week + timedelta(days=i)
        dates.append(current_date.strftime('%Y-%m-%d'))
        amount = 0
        
        # Find sales for this date
        for sale in sales_data:
            if sale['transaction_date__date'] == current_date:
                amount = float(sale['total_sales'] or 0)
                break
                
        amounts.append(amount)
    
    # Create chart
    plt.switch_backend('Agg')  # Important for Django
    plt.figure(figsize=(8, 4))
    plt.plot(dates, amounts, marker='o', color='#26a69a')  # Materialize teal color
    plt.title('Sales Last Week', pad=20)
    plt.xlabel('Date')
    plt.ylabel('Amount ($)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save chart to bytes
    chart_buffer = io.BytesIO()
    plt.savefig(chart_buffer, format='png', dpi=100)
    plt.close()
    chart_buffer.seek(0)
    chart_data = base64.b64encode(chart_buffer.getvalue()).decode('utf-8')
    chart_buffer.close()
    
    context = {
        'total_products': total_products,
        'low_stock': low_stock,
        'recent_transactions': recent_transactions,
        'chart_data': chart_data,
    }
    return render(request, 'inventory/dashboard.html', context)

@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'inventory/products.html', {'products': products})

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('products')
    else:
        form = ProductForm()
    return render(request, 'inventory/add_product.html', {'form': form})

@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'inventory/edit_product.html', {'form': form, 'product': product})

@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('products')
    return render(request, 'inventory/confirm_delete.html', {'product': product})

@login_required
def bills(request):
    bills = Bill.objects.order_by('-created_at')
    return render(request, 'inventory/bills.html', {'bills': bills})

@login_required
def generate_bill(request):
    if request.method == 'POST':
        bill_form = BillForm(request.POST)
        if bill_form.is_valid():
            bill = bill_form.save(commit=False)
            bill.created_by = request.user
            bill.total_amount = 0  # Initialize to 0
            bill.save()  # Save first to get an ID
            
            # Process bill items
            product_ids = request.POST.getlist('product')
            quantities = request.POST.getlist('quantity')
            
            total_amount = 0
            
            for product_id, quantity in zip(product_ids, quantities):
                if not product_id or not quantity:
                    continue
                    
                try:
                    product = Product.objects.get(pk=product_id)
                    quantity = int(quantity)
                    
                    if quantity <= 0:
                        continue
                        
                    # Check if enough stock is available
                    if product.quantity < quantity:
                        messages.error(request, f"Not enough stock for {product.name}. Only {product.quantity} available.")
                        continue
                    
                    bill_item = BillItem(
                        bill=bill,
                        product=product,
                        quantity=quantity,
                        price=product.price
                    )
                    bill_item.save()
                    total_amount += bill_item.total
                    
                    # Record transaction
                    Transaction.objects.create(
                        product=product,
                        transaction_type='SALE',
                        quantity=quantity,
                        price=product.price,
                        notes=f"Bill #{bill.id}"
                    )
                
                except (Product.DoesNotExist, ValueError) as e:
                    messages.error(request, f"Invalid product or quantity: {e}")
                    continue
            
            # Update the bill with the total amount
            bill.total_amount = total_amount
            bill.save()
            
            if total_amount > 0:
                return redirect('view_bill', bill_id=bill.id)
            else:
                messages.error(request, "Bill must have at least one valid item")
                bill.delete()  # Delete the empty bill
                return redirect('generate_bill')
    else:
        bill_form = BillForm()
    
    products = Product.objects.filter(quantity__gt=0)
    return render(request, 'inventory/generate_bill.html', {
        'bill_form': bill_form,
        'products': products
    })

@login_required
def view_bill(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    return render(request, 'inventory/view_bill.html', {'bill': bill})

@login_required
def download_bill(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Bill_{bill.id}.pdf"'
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    elements = []
    
    # Bill header
    data = [
        ["INVOICE"],
        ["Bill #", bill.id],
        ["Date", bill.created_at.strftime('%Y-%m-%d %H:%M')],
        ["Customer", bill.customer_name],
        ["Contact", bill.customer_contact or "N/A"],
        ["", ""],
        ["Item", "Quantity", "Price", "Total"]
    ]
    
    # Bill items
    for item in bill.items.all():
        data.append([
            item.product.name,
            str(item.quantity),
            f"${item.price:.2f}",
            f"${item.total:.2f}"
        ])
    
    # Total
    data.append(["", "", "Total:", f"${bill.total_amount:.2f}"])
    
    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response

@login_required
def reports(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        if report_type == 'inventory':
            products = Product.objects.all()
            return generate_pdf_report(products, 'Inventory Report', 'inventory_report.pdf')
        elif report_type == 'transactions':
            transactions = Transaction.objects.filter(
                transaction_date__range=[start_date, end_date]
            )
            return generate_pdf_report(transactions, 'Transactions Report', 'transactions_report.pdf')
        elif report_type == 'sales':
            sales = Transaction.objects.filter(
                transaction_type='SALE',
                transaction_date__range=[start_date, end_date]
            )
            return generate_pdf_report(sales, 'Sales Report', 'sales_report.pdf')
    
    return render(request, 'inventory/reports.html')
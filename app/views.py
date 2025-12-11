import datetime
import json
from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from datetime import datetime, timedelta
import time

def contact(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
        user_not_login = 'hidden'
        user_login = 'show'
    else:
        items = []
        order = {'get_cart_total':0, 'get_cart_items':0}
        cartItems = order['get_cart_items']
        user_not_login = 'show'
        user_login = 'hidden'
    categories = Category.objects.filter(is_sub=False)
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        message = request.POST.get('message')
        
        # Lưu vào database
        Contact.objects.create(
            fullname=fullname,
            email=email,
            phone=phone,
            message=message
        )
        
        messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
        return redirect('contact')
    context = {
        'items': items,
        'order': order,
        'cartItems': cartItems,
        'user_not_login': user_not_login,
        'user_login': user_login,
        'categories': categories,
    }
    return render(request, 'app/contact.html', context)

def detail(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
        user_not_login = 'hidden'
        user_login = 'show'
    else:
        items = []
        order = {'get_cart_total':0, 'get_cart_items':0}
        cartItems = order['get_cart_items']
        user_not_login = 'show'
        user_login = 'hidden'
    id = request.GET.get('id', '')
    products = Product.objects.filter(id=id)
    categories = Category.objects.filter(is_sub=False)
    context = {
        'items': items,
        'order': order,
        'cartItems': cartItems,
        'user_not_login': user_not_login,
        'user_login': user_login,
        'categories': categories,
        'products': products,
    }
    return render(request, 'app/detail.html', context)


def category(request):
    categories = Category.objects.filter(is_sub=False)
    active_category = request.GET.get('category', '')
    if active_category:
        products = Product.objects.filter(category__slug=active_category)
    context = {
        'categories': categories,
        'products': products,
        'active_category': active_category,
    }
    return render(request, 'app/category.html', context)

def search(request):
    if request.method == 'POST':
        searched = request.POST["searched"]
        keys = Product.objects.filter(name__icontains=searched)
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
        user_not_login = 'hidden'
        user_login = 'show'
    else:
        items = []
        order = {'get_cart_total':0, 'get_cart_items':0}
        cartItems = order['get_cart_items']
        user_not_login = 'show'
        user_login = 'hidden'
    products = Product.objects.all()
    context = {
        'keys': keys,
        'searched': searched,
        'cartItems': cartItems,
        'products': products,
        'user_not_login': user_not_login,
        'user_login': user_login,
    }
    return render(request, 'app/search.html', context)

def register(request):
    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    context = {'form': form}
    return render(request, 'app/register.html', context)

def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else: messages.info(request, 'Username OR password is incorrect')


    context = {}
    return render(request, 'app/login.html', context)

def logoutPage(request):
    logout(request)
    return redirect('login')

def home(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
        user_not_login = 'hidden'
        user_login = 'show'
    else:
        items = []
        order = {'get_cart_total':0, 'get_cart_items':0}
        cartItems = order['get_cart_items']
        user_not_login = 'show'
        user_login = 'hidden'
    categories = Category.objects.filter(is_sub=False)
    products = Product.objects.all()
    context = {
        'products': products,
        'cartItems': cartItems,
        'user_not_login': user_not_login,
        'user_login': user_login,
        'categories': categories,
    }
    return render(request, 'app/home.html', context)

def cart(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.exclude(product__isnull=True)
        cartItems = order.get_cart_items
        user_not_login = 'hidden'
        user_login = 'show'
    else:
        items = []
        order = {'get_cart_total':0, 'get_cart_items':0}
        cartItems = order['get_cart_items']
        user_not_login = 'show'
        user_login = 'hidden'
    categories = Category.objects.filter(is_sub=False)
    context = {
        'items': items,
        'order': order,
        'cartItems': cartItems,
        'user_not_login': user_not_login,
        'user_login': user_login,
        'categories': categories,
    }
    return render(request, 'app/cart.html', context)

def checkout(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
        user_not_login = 'hidden'
        user_login = 'show'
    else:
        items = []
        order = {'get_cart_total':0, 'get_cart_items':0}
        cartItems = order['get_cart_items']
        user_not_login = 'show'
        user_login = 'hidden'
    categories = Category.objects.filter(is_sub=False)
    context = {
        'items': items,
        'order': order,
        'cartItems': cartItems,
        'user_not_login': user_not_login,
        'user_login': user_login,
        'categories': categories,
    }
    return render(request, 'app/checkout.html', context)

def process_order(request):
    if request.method == 'POST':
        # Lấy thông tin từ form
        name = request.POST.get('name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        
        # Xử lý đơn hàng cho user đã đăng nhập
        if request.user.is_authenticated:
            customer = request.user
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
            
            # Tạo transaction ID - SỬA LẠI DÒNG NÀY
            transaction_id = str(int(time.time() * 1000))  # Sử dụng time.time() thay vì datetime.datetime.now().timestamp()
            order.transaction_id = transaction_id
            
            # Đánh dấu đơn hàng đã hoàn thành
            order.complete = True
            order.save()
            
            # Lưu thông tin vận chuyển
            ShippingAddress.objects.create(
                customer=customer,
                order=order,
                address=address,
                city=city,
                state=state,
                mobile=phone
            )
            
            messages.success(request, 'Đặt hàng thành công!')
            
            # Chuyển đến trang thành công
            categories = Category.objects.filter(is_sub=False)
            context = {
                'order': order,
                'cartItems': 0,  # Giỏ hàng đã về 0
                'user_not_login': 'hidden',
                'user_login': 'show',
                'categories': categories,
            }
            return render(request, 'app/order_success.html', context)
        else:
            # Xử lý cho guest user (chưa đăng nhập)
            messages.warning(request, 'Vui lòng đăng nhập để hoàn tất đơn hàng!')
            return redirect('login')
    
    return redirect('checkout')

# def process_order(request):
#     if request.method == 'POST':
#         # Lấy thông tin từ form
#         name = request.POST.get('name')
#         email = request.POST.get('email')
#         address = request.POST.get('address')
#         phone = request.POST.get('phone')
#         city = request.POST.get('city', '')
#         state = request.POST.get('state', '')
        
#         # Xử lý đơn hàng cho user đã đăng nhập
#         if request.user.is_authenticated:
#             customer = request.user
#             order, created = Order.objects.get_or_create(customer=customer, complete=False)
            
#             # Tạo transaction ID
#             transaction_id = datetime.datetime.now().timestamp()
#             order.transaction_id = transaction_id
            
#             # Đánh dấu đơn hàng đã hoàn thành
#             order.complete = True
#             order.save()
            
#             # Lưu thông tin vận chuyển
#             ShippingAddress.objects.create(
#                 customer=customer,
#                 order=order,
#                 address=address,
#                 city=city,
#                 state=state,
#                 mobile=phone
#             )
            
#             # Chuyển đến trang thành công
#             context = {
#                 'order': order,
#                 'cartItems': 0,  # Giỏ hàng đã về 0
#                 'user_not_login': 'hidden',
#                 'user_login': 'show',
#                 'categories': Category.objects.filter(is_sub=False),
#             }
#             return render(request, 'app/order_success.html', context)
#         else:
#             # Xử lý cho guest user (chưa đăng nhập)
#             messages.warning(request, 'Vui lòng đăng nhập để hoàn tất đơn hàng!')
#             return redirect('login')
    
#     return redirect('checkout')


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    customer = request.user
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity += 1
    elif action == 'remove':
        orderItem.quantity -= 1

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('added', safe=False)


def statistics(request):
    # Kiểm tra quyền admin
    if not request.user.is_staff:
        messages.error(request, 'Bạn không có quyền truy cập trang này!')
        return redirect('home')
    
    # Lấy parameters từ request
    filter_type = request.GET.get('filter_type', 'month')
    
    # Khởi tạo biến
    start_date = None
    end_date = None
    selected_week = ''
    selected_month = ''
    selected_quarter = ''
    selected_year = datetime.now().year
    
    # Xử lý theo loại filter
    if filter_type == 'week':
        week = request.GET.get('week', '')
        if week:
            selected_week = week
            year, week_num = week.split('-W')
            start_date = datetime.strptime(f'{year}-W{week_num}-1', "%Y-W%W-%w")
            end_date = start_date + timedelta(days=6)
        else:
            # Tuần hiện tại
            today = datetime.now()
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
            
    elif filter_type == 'month':
        month = request.GET.get('month', '')
        if month:
            selected_month = month
            year, month_num = month.split('-')
            start_date = datetime(int(year), int(month_num), 1)
            if int(month_num) == 12:
                end_date = datetime(int(year) + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(int(year), int(month_num) + 1, 1) - timedelta(days=1)
        else:
            # Tháng hiện tại
            today = datetime.now()
            start_date = datetime(today.year, today.month, 1)
            if today.month == 12:
                end_date = datetime(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(today.year, today.month + 1, 1) - timedelta(days=1)
                
    elif filter_type == 'quarter':
        quarter = request.GET.get('quarter', '1')
        year = request.GET.get('quarter_year', str(datetime.now().year))
        selected_quarter = quarter
        selected_year = year
        
        quarter = int(quarter)
        year = int(year)
        
        quarter_months = {
            1: (1, 3),
            2: (4, 6),
            3: (7, 9),
            4: (10, 12)
        }
        
        start_month, end_month = quarter_months[quarter]
        start_date = datetime(year, start_month, 1)
        if end_month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, end_month + 1, 1) - timedelta(days=1)
            
    elif filter_type == 'year':
        year = request.GET.get('year', str(datetime.now().year))
        selected_year = year
        year = int(year)
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        
    elif filter_type == 'custom':
        start_date_str = request.GET.get('start_date', '')
        end_date_str = request.GET.get('end_date', '')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            # 30 ngày gần nhất
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
    
    # Query đơn hàng trong khoảng thời gian
    orders = Order.objects.filter(
        complete=True,
        date_order__gte=start_date,
        date_order__lte=end_date
    ).order_by('-date_order')
    
    # Tính toán thống kê
    total_orders = orders.count()
    total_revenue = sum([order.get_cart_total for order in orders])
    
    # Tổng số sản phẩm đã bán
    total_products_sold = 0
    for order in orders:
        total_products_sold += order.get_cart_items
    
    # Giá trị trung bình mỗi đơn hàng
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Dữ liệu cho biểu đồ
    chart_labels = []
    chart_data = []
    
    if filter_type == 'week':
        # Thống kê theo ngày trong tuần
        for i in range(7):
            day = start_date + timedelta(days=i)
            day_orders = orders.filter(date_order__date=day.date())
            day_revenue = sum([order.get_cart_total for order in day_orders])
            chart_labels.append(day.strftime('%d/%m'))
            chart_data.append(day_revenue)
            
    elif filter_type == 'month':
        # Thống kê theo ngày trong tháng
        days_in_month = (end_date - start_date).days + 1
        for i in range(days_in_month):
            day = start_date + timedelta(days=i)
            day_orders = orders.filter(date_order__date=day.date())
            day_revenue = sum([order.get_cart_total for order in day_orders])
            chart_labels.append(day.strftime('%d/%m'))
            chart_data.append(day_revenue)
            
    elif filter_type == 'quarter':
        # Thống kê theo tháng trong quý
        for month in range(3):
            current_month = start_date.month + month
            month_start = datetime(start_date.year, current_month, 1)
            if current_month == 12:
                month_end = datetime(start_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = datetime(start_date.year, current_month + 1, 1) - timedelta(days=1)
            
            month_orders = orders.filter(
                date_order__gte=month_start,
                date_order__lte=month_end
            )
            month_revenue = sum([order.get_cart_total for order in month_orders])
            chart_labels.append(f'Tháng {current_month}')
            chart_data.append(month_revenue)
            
    elif filter_type == 'year':
        # Thống kê theo tháng trong năm
        for month in range(1, 13):
            month_start = datetime(start_date.year, month, 1)
            if month == 12:
                month_end = datetime(start_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = datetime(start_date.year, month + 1, 1) - timedelta(days=1)
            
            month_orders = orders.filter(
                date_order__gte=month_start,
                date_order__lte=month_end
            )
            month_revenue = sum([order.get_cart_total for order in month_orders])
            chart_labels.append(f'T{month}')
            chart_data.append(month_revenue)
    else:
        # Custom: chia theo tuần
        current = start_date
        while current <= end_date:
            week_end = min(current + timedelta(days=6), end_date)
            week_orders = orders.filter(
                date_order__gte=current,
                date_order__lte=week_end
            )
            week_revenue = sum([order.get_cart_total for order in week_orders])
            chart_labels.append(f'{current.strftime("%d/%m")}')
            chart_data.append(week_revenue)
            current = week_end + timedelta(days=1)
    
    # Top sản phẩm bán chạy
    top_products_data = OrderItem.objects.filter(
        order__complete=True,
        order__date_order__gte=start_date,
        order__date_order__lte=end_date,
        product__isnull=False
    ).values('product').annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:10]

    # Tạo danh sách với thông tin đầy đủ
    top_products = []
    for item in top_products_data:
        try:
            product = Product.objects.get(id=item['product'])
            top_products.append({
                'product': product,
                'total_quantity': item['total_quantity'],
                'total_revenue': item['total_quantity'] * product.price
            })
        except Product.DoesNotExist:
            continue
    
    # Dữ liệu cho biểu đồ tròn top sản phẩm
    top_products_labels = [item['product'].name for item in top_products[:5]]
    top_products_data = [item['total_quantity'] for item in top_products[:5]]
    
    # Lấy categories cho menu
    categories = Category.objects.filter(is_sub=False)
    
    # Giỏ hàng
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        cartItems = order.get_cart_items
    else:
        cartItems = 0
    
    context = {
        'filter_type': filter_type,
        'selected_week': selected_week,
        'selected_month': selected_month,
        'selected_quarter': selected_quarter,
        'selected_year': selected_year,
        'start_date': start_date.strftime('%Y-%m-%d') if start_date else '',
        'end_date': end_date.strftime('%Y-%m-%d') if end_date else '',
        'orders': orders,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_products_sold': total_products_sold,
        'average_order_value': average_order_value,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'top_products': top_products,
        'top_products_labels': json.dumps(top_products_labels),
        'top_products_data': json.dumps(top_products_data),
        'categories': categories,
        'cartItems': cartItems,
        'user_login': 'show',
        'user_not_login': 'hidden',
    }
    
    return render(request, 'app/statistics.html', context)
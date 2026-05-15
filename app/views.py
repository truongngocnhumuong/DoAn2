import json
import uuid
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta


# ─────────────────────────────────────────────
# CT7: HELPER FUNCTION — dùng chung cho mọi view
# ─────────────────────────────────────────────
def get_cart_context(user):
    """
    Trả về context liên quan đến giỏ hàng và trạng thái đăng nhập.
    Dùng chung cho tất cả các view để tránh lặp code.
    """
    if user.is_authenticated:
        order, created = Order.objects.get_or_create(customer=user, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
        return {
            'items': items,
            'order': order,
            'cartItems': cartItems,
            'user_not_login': 'hidden',
            'user_login': 'show',
        }
    else:
        return {
            'items': [],
            'order': {'get_cart_total': 0, 'get_cart_items': 0},
            'cartItems': 0,
            'user_not_login': 'show',
            'user_login': 'hidden',
        }


# ─────────────────────────────────────────────
# AUTH VIEWS
# ─────────────────────────────────────────────
def register(request):
    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đăng ký thành công! Vui lòng đăng nhập.')
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
        else:
            messages.info(request, 'Tên đăng nhập hoặc mật khẩu không đúng!')
    return render(request, 'app/login.html', {})


def logoutPage(request):
    logout(request)
    return redirect('login')


# ─────────────────────────────────────────────
# MAIN VIEWS
# ─────────────────────────────────────────────
def home(request):
    cart_ctx = get_cart_context(request.user)
    categories = Category.objects.filter(is_sub=False)

    # CT4: Phân trang — 8 sản phẩm/trang
    all_products = Product.objects.all()
    paginator = Paginator(all_products, 8)
    page_number = request.GET.get('page', 1)
    products = paginator.get_page(page_number)

    context = {
        **cart_ctx,
        'products': products,
        'categories': categories,
    }
    return render(request, 'app/home.html', context)


def cart(request):
    cart_ctx = get_cart_context(request.user)
    categories = Category.objects.filter(is_sub=False)
    # Loại bỏ items có product=None khỏi view cart
    if request.user.is_authenticated:
        order = cart_ctx['order']
        items = order.orderitem_set.exclude(product__isnull=True)
        cart_ctx['items'] = items
    context = {
        **cart_ctx,
        'categories': categories,
    }
    return render(request, 'app/cart.html', context)


def checkout(request):
    cart_ctx = get_cart_context(request.user)
    categories = Category.objects.filter(is_sub=False)

    # CT3: Tự điền thông tin từ UserProfile
    user_profile = None
    if request.user.is_authenticated:
        try:
            user_profile = request.user.profile
        except UserProfile.DoesNotExist:
            pass

    context = {
        **cart_ctx,
        'categories': categories,
        'user_profile': user_profile,
    }
    return render(request, 'app/checkout.html', context)


def process_order(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')

        if request.user.is_authenticated:
            customer = request.user
            order, created = Order.objects.get_or_create(customer=customer, complete=False)

            # CT1: Kiểm tra tồn kho trước khi xác nhận đơn
            order_items = order.orderitem_set.filter(product__isnull=False)
            for item in order_items:
                if item.product.stock < item.quantity:
                    messages.error(
                        request,
                        f'Sản phẩm "{item.product.name}" chỉ còn {item.product.stock} cái, '
                        f'không đủ số lượng yêu cầu ({item.quantity})!'
                    )
                    return redirect('cart')

            # CT6: Dùng UUID thay time.time()
            order.transaction_id = str(uuid.uuid4())
            order.complete = True
            # CT2: Cập nhật trạng thái đơn hàng
            order.status = Order.STATUS_PROCESSING
            order.save()

            # CT1: Trừ stock cho từng sản phẩm sau khi đặt hàng thành công
            for item in order_items:
                product = item.product
                product.stock = max(0, product.stock - item.quantity)
                product.save()

            ShippingAddress.objects.create(
                customer=customer,
                order=order,
                address=address,
                city=city,
                state=state,
                mobile=phone
            )

            messages.success(request, 'Đặt hàng thành công!')
            categories = Category.objects.filter(is_sub=False)
            context = {
                'order': order,
                'cartItems': 0,
                'user_not_login': 'hidden',
                'user_login': 'show',
                'categories': categories,
            }
            return render(request, 'app/order_success.html', context)
        else:
            messages.warning(request, 'Vui lòng đăng nhập để hoàn tất đơn hàng!')
            return redirect('login')

    return redirect('checkout')


def detail(request):
    cart_ctx = get_cart_context(request.user)
    categories = Category.objects.filter(is_sub=False)
    product_id = request.GET.get('id', '')
    products = Product.objects.filter(id=product_id)
    context = {
        **cart_ctx,
        'categories': categories,
        'products': products,
    }
    return render(request, 'app/detail.html', context)


def category(request):
    categories = Category.objects.filter(is_sub=False)
    active_category = request.GET.get('category', '')
    cart_ctx = get_cart_context(request.user)

    if active_category:
        all_products = Product.objects.filter(category__slug=active_category)
    else:
        all_products = Product.objects.none()

    # CT4: Phân trang
    paginator = Paginator(all_products, 8)
    page_number = request.GET.get('page', 1)
    products = paginator.get_page(page_number)

    context = {
        **cart_ctx,
        'categories': categories,
        'products': products,
        'active_category': active_category,
    }
    return render(request, 'app/category.html', context)


def search(request):
    cart_ctx = get_cart_context(request.user)
    categories = Category.objects.filter(is_sub=False)
    searched = ''
    keys = Product.objects.none()

    if request.method == 'POST':
        searched = request.POST.get('searched', '')
        if searched:
            all_keys = Product.objects.filter(name__icontains=searched)
            # CT4: Phân trang
            paginator = Paginator(all_keys, 8)
            page_number = request.GET.get('page', 1)
            keys = paginator.get_page(page_number)

    context = {
        **cart_ctx,
        'keys': keys,
        'searched': searched,
        'categories': categories,
    }
    return render(request, 'app/search.html', context)


def contact(request):
    cart_ctx = get_cart_context(request.user)
    categories = Category.objects.filter(is_sub=False)

    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        message_text = request.POST.get('message')
        Contact.objects.create(
            fullname=fullname,
            email=email,
            phone=phone,
            message=message_text
        )
        messages.success(request, 'Cảm ơn bạn đã liên hệ! Chúng tôi sẽ phản hồi sớm.')
        return redirect('contact')

    context = {
        **cart_ctx,
        'categories': categories,
    }
    return render(request, 'app/contact.html', context)


# ─────────────────────────────────────────────
# CT1: CART UPDATE — có kiểm tra tồn kho
# ─────────────────────────────────────────────
def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    customer = request.user
    product = get_object_or_404(Product, id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        # CT1: Kiểm tra tồn kho trước khi thêm
        if not product.in_stock:
            return JsonResponse({'error': 'Sản phẩm đã hết hàng!'}, status=400)
        orderItem.quantity += 1
    elif action == 'remove':
        orderItem.quantity -= 1

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse({'message': 'Đã cập nhật giỏ hàng', 'cartItems': order.get_cart_items})


# ─────────────────────────────────────────────
# CT2: ĐƠN HÀNG CỦA TÔI
# ─────────────────────────────────────────────
@login_required(login_url='login')
def my_orders(request):
    """Xem lịch sử đơn hàng của người dùng đang đăng nhập."""
    cart_ctx = get_cart_context(request.user)
    categories = Category.objects.filter(is_sub=False)

    orders = Order.objects.filter(
        customer=request.user,
        complete=True
    ).order_by('-date_order')

    context = {
        **cart_ctx,
        'categories': categories,
        'orders': orders,
    }
    return render(request, 'app/my_orders.html', context)


@login_required(login_url='login')
def update_order_status(request, pk):
    """Admin cập nhật trạng thái đơn hàng."""
    if not request.user.is_staff:
        messages.error(request, 'Bạn không có quyền thực hiện thao tác này!')
        return redirect('home')

    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = [s[0] for s in Order.STATUS_CHOICES]
        if new_status in valid_statuses:
            order.status = new_status
            order.save()
            messages.success(request, f'Đã cập nhật trạng thái đơn hàng #{order.id}')
        else:
            messages.error(request, 'Trạng thái không hợp lệ!')
    return redirect('statistics')


# ─────────────────────────────────────────────
# CT3: USER PROFILE
# ─────────────────────────────────────────────
@login_required(login_url='login')
def profile(request):
    """Xem và cập nhật thông tin cá nhân."""
    cart_ctx = get_cart_context(request.user)
    categories = Category.objects.filter(is_sub=False)

    # Lấy hoặc tạo profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Cập nhật User
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()

        # Cập nhật Profile
        user_profile.phone = request.POST.get('phone', '')
        user_profile.address = request.POST.get('address', '')
        user_profile.city = request.POST.get('city', '')
        if 'avatar' in request.FILES:
            user_profile.avatar = request.FILES['avatar']
        user_profile.save()

        messages.success(request, 'Cập nhật thông tin thành công!')
        return redirect('profile')

    context = {
        **cart_ctx,
        'categories': categories,
        'user_profile': user_profile,
    }
    return render(request, 'app/profile.html', context)


# ─────────────────────────────────────────────
# STATISTICS (giữ nguyên, chỉ thêm update status)
# ─────────────────────────────────────────────
def statistics(request):
    if not request.user.is_staff:
        messages.error(request, 'Bạn không có quyền truy cập trang này!')
        return redirect('home')

    filter_type = request.GET.get('filter_type', 'month')
    start_date = None
    end_date = None
    selected_week = ''
    selected_month = ''
    selected_quarter = ''
    selected_year = datetime.now().year

    if filter_type == 'week':
        week = request.GET.get('week', '')
        if week:
            selected_week = week
            year, week_num = week.split('-W')
            start_date = datetime.strptime(f'{year}-W{week_num}-1', "%Y-W%W-%w")
            end_date = start_date + timedelta(days=6)
        else:
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
        quarter_months = {1: (1, 3), 2: (4, 6), 3: (7, 9), 4: (10, 12)}
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
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

    orders = Order.objects.filter(
        complete=True,
        date_order__gte=start_date,
        date_order__lte=end_date
    ).order_by('-date_order')

    total_orders = orders.count()
    total_revenue = sum([order.get_cart_total for order in orders])
    total_products_sold = sum([order.get_cart_items for order in orders])
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0

    chart_labels = []
    chart_data = []

    if filter_type == 'week':
        for i in range(7):
            day = start_date + timedelta(days=i)
            day_orders = orders.filter(date_order__date=day.date())
            day_revenue = sum([o.get_cart_total for o in day_orders])
            chart_labels.append(day.strftime('%d/%m'))
            chart_data.append(day_revenue)

    elif filter_type == 'month':
        days_in_month = (end_date - start_date).days + 1
        for i in range(days_in_month):
            day = start_date + timedelta(days=i)
            day_orders = orders.filter(date_order__date=day.date())
            day_revenue = sum([o.get_cart_total for o in day_orders])
            chart_labels.append(day.strftime('%d/%m'))
            chart_data.append(day_revenue)

    elif filter_type == 'quarter':
        for month in range(3):
            current_month = start_date.month + month
            month_start = datetime(start_date.year, current_month, 1)
            if current_month == 12:
                month_end = datetime(start_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = datetime(start_date.year, current_month + 1, 1) - timedelta(days=1)
            month_orders = orders.filter(date_order__gte=month_start, date_order__lte=month_end)
            month_revenue = sum([o.get_cart_total for o in month_orders])
            chart_labels.append(f'Tháng {current_month}')
            chart_data.append(month_revenue)

    elif filter_type == 'year':
        for month in range(1, 13):
            month_start = datetime(start_date.year, month, 1)
            if month == 12:
                month_end = datetime(start_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = datetime(start_date.year, month + 1, 1) - timedelta(days=1)
            month_orders = orders.filter(date_order__gte=month_start, date_order__lte=month_end)
            month_revenue = sum([o.get_cart_total for o in month_orders])
            chart_labels.append(f'T{month}')
            chart_data.append(month_revenue)
    else:
        current = start_date
        while current <= end_date:
            week_end = min(current + timedelta(days=6), end_date)
            week_orders = orders.filter(date_order__gte=current, date_order__lte=week_end)
            week_revenue = sum([o.get_cart_total for o in week_orders])
            chart_labels.append(f'{current.strftime("%d/%m")}')
            chart_data.append(week_revenue)
            current = week_end + timedelta(days=1)

    top_products_data = OrderItem.objects.filter(
        order__complete=True,
        order__date_order__gte=start_date,
        order__date_order__lte=end_date,
        product__isnull=False
    ).values('product').annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:10]

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

    top_products_labels = [item['product'].name for item in top_products[:5]]
    top_products_chart_data = [item['total_quantity'] for item in top_products[:5]]

    categories = Category.objects.filter(is_sub=False)
    cart_ctx = get_cart_context(request.user)

    # CT2: Danh sách đơn hàng kèm trạng thái để admin cập nhật
    recent_orders_with_status = orders[:20]

    context = {
        **cart_ctx,
        'filter_type': filter_type,
        'selected_week': selected_week,
        'selected_month': selected_month,
        'selected_quarter': selected_quarter,
        'selected_year': selected_year,
        'start_date': start_date.strftime('%Y-%m-%d') if start_date else '',
        'end_date': end_date.strftime('%Y-%m-%d') if end_date else '',
        'orders': orders,
        'recent_orders_with_status': recent_orders_with_status,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_products_sold': total_products_sold,
        'average_order_value': average_order_value,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'top_products': top_products,
        'top_products_labels': json.dumps(top_products_labels),
        'top_products_data': json.dumps(top_products_chart_data),
        'categories': categories,
        'order_status_choices': Order.STATUS_CHOICES,
    }

    return render(request, 'app/statistics.html', context)
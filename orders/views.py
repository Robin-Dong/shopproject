from django.shortcuts import render,redirect, get_object_or_404
from .models import OrderItem, Order
from .forms import OrderCreateForm
from cart.cart import Cart
from .task import order_created
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint

# Create your views here.


# 后台订单详细定制
@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin/orders/order/detail.html', {'order': order})


# 后台pdf订单
@staff_member_required
def admin_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('orders/order/pdf.html', {'order': order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="order_{}"'.format(order.id)
    weasyprint.HTML(string=html).write_pdf(response, stylesheets=[weasyprint.CSS(settings.STATIC_ROOT + '/shop/css/pdf.css')])
    return response


def order_create(request):
    cart = Cart(request)
    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid() and len(cart):

            order = form.save(commit=False)
            if cart.coupon:
                order.coupon = cart.coupon
                order.discount = cart.coupon.discount
            order.save()

            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], price=item['price'],
                                         quantity=item['quantity'])
            # 成功生成OrderItem之后清除购物车
            cart.clear()
            # 清除优惠券信息
            request.session['coupon_id'] = None
            #  启动异步任务
            order_created.delay(order.id)
            # 在session中加入订单id
            request.session['order_id'] = order.id
            # 重定向到支付页面
            return redirect(reverse('payment:process'))
            #return render(request, 'orders/order/created.html', {'order': order})
    else:
        form = OrderCreateForm()
    return render(request, 'orders/order/create.html', {'cart': cart, 'form': form})

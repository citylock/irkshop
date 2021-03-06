from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import Goods
from .models import Shipping
from .models import Category
from .models import Order
from .models import OrderDetail
from .forms import OrderForm
from .tasks import check_payment

from carton.cart import Cart
from django.contrib.auth.models import User

from core.send_mail import send_mail

from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received

import csv
from datetime import datetime
import requests
import json


def index(request):
    categories = Category.objects.all()
    categories_list = []
    for i in categories:
        categories_list.append('SHOP'+i.name)
    goods = Goods.objects.all()
    return render(request, 'goods/index.html', {
        'goods': goods,
        'categories': categories,
        'categories_list': categories_list
    })

def add_cart(request):
    if request.method == 'POST':
        if request.is_ajax():
            cart = Cart(request.session)
            goods = Goods.objects.get(id=request.POST.get('good'))
            cart.add(goods, price=goods.price)
            return JsonResponse({
                'message':"Added {}".format(goods.name)
            })
    return JsonResponse({
        'message':"Please Access with AJAX/POST"
    })

def update_cart(request):
    if request.method == 'POST':
        if request.is_ajax():
            cart = Cart(request.session)
            quantity = request.POST.get('quantity')
            goods = Goods.objects.get(id=request.POST.get('good'))
            cart.set_quantity(goods, quantity)
            return JsonResponse({
                'message':'update {} for {}'.format(
                    goods.name, quantity
                )
            })

def show_cart(request):
    cart = Cart(request.session)
    context = {"items": cart.items}
    return render(request, 'shopping/shopping-cart.html', context=context)

def current_cart(request):
    cart = Cart(request.session)
    return JsonResponse(dict(data=cart.items_serializable))

def remove_cart(request):
    if request.method == 'POST':
        if request.is_ajax():
            cart = Cart(request.session)
            goods = Goods.objects.get(pk=request.POST.get('good'))
            cart.remove(goods)
            return JsonResponse({
                'message': "Removed"
            })

def clear_cart(request):
    if request.method == 'POST':
        if request.is_ajax():
            cart = Cart(request.session)
            cart.clear()
            return JsonResponse({
                'message': 'cleared cart'
            })

@login_required
def payment_local(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        print(form.is_valid())
        if form.is_valid():
            print(form.cleaned_data)
            this_order = Order()
            cart = Cart(request.session).cart_serializable
            this_order.address = form.cleaned_data.get('address', '')
            this_order.additional_address = form.cleaned_data.get('AdditionalAddress', '')
            this_order.custom_order = form.cleaned_data.get('OrderOptioin', '')

            this_order.user = request.user
            this_order.save()
            order_number = this_order.pk
            for v in cart.values():
                order_detail = OrderDetail()
                order_detail.good = Goods.objects.get(pk=v['product_pk'])
                order_detail.count = v['quantity']
                order_detail.order = this_order
                order_detail.save()

            # clear cart
            Cart(request.session).clear()

            # paypal
            this_order = Order.objects.get(pk=order_number)

            if this_order.address != None:
                shipping_fee_order = OrderDetail()
                # TODO: Change Hard Coding this pk to env?
                shipping_fee_order.good = Goods.objects.get(pk=10)
                shipping_fee_order.count = 1
                shipping_fee_order.order = this_order
                shipping_fee_order.save()

            total_price = this_order.total_price
            try:
                paypal_dict = {
                    "business": "{}".format(settings.PAYPAL_ID),
                    "amount": "{}".format(total_price),
                    "item_name": "{}".format(this_order.orderdetail.all()[0].good),
                    "invoice": "{}".format(this_order.pk),
                    # TODO: Change URL from code to Envs.json
                    "notify_url": "http://shop.resist.kr/paypal/",
                    "return_url": "http://shop.resist.kr/thankyou/",
                    "cancel_return": "http://shop.resist.kr/",
                    "custom": "{}".format(this_order.user)
                }
            except:
                return JsonResponse({
                    'message': 'please checkout with more than 1 items'
                })
            paypal_form = PayPalPaymentsForm(initial=paypal_dict).render()

            orders = this_order.orderdetail.all()
            orders_detail = ''
            for order in orders:
                orders_detail += (
                    '{} x {}\n'.format(
                        order.good,
                        order.count
                    )
                )

            send_mail(
                user=settings.GMAIL_ID,
                pwd=settings.GMAIL_PW,
                recipient=User.objects.get(username=this_order.user).email,
                subject="Order to SHOPIRK: Via Noir Seoul",
                body="Hello {},\n We've Just got your order from SHOPIRK: Via Noir Seoul.\nThis is how you've ordered, Please check carefully.\n"
                     "Invoice Number: #{}\n"
                     "YOUR ORDERS:\n"
                     "{}\n"
                     "Thanks again for your Order.\n"
                     "Sincerely, IRK.".format(
                    this_order.user,
                    this_order.pk,
                    orders_detail
                ),
            )

            return JsonResponse({
                'message': "Sucessfully Ordered!\n"
                           "Please Continue with Paypal Payment.\n"
                           "(Paypal Checkout will show soon.)",
                'paypal-form': paypal_form
            })
        else:
            return JsonResponse({
                'message': 'form is not Valid'
            })
    else:
        form = OrderForm()

    return render(request, 'payment/payment_local.html', {
        'form': form,
    })

@login_required
def payment_paypal(request, order_number):
    order = Order.objects.get(pk=order_number)
    if order.is_paid:
        return JsonResponse({
            'message': 'Already Paid purchase'
        })

    # What you want the button to do.
    paypal_dict = {
        "business": "{}".format(settings.PAYPAL_ID),
        "amount": "{}".format(order.total_price),
        "item_name": "{}".format(order.orderdetail.all()[0].good),
        "invoice": "{}".format(order.pk),
        "notify_url": "http://shop.resist.kr/paypal/",
        "return_url": "http://shop.resist.kr/thankyou/",
        "cancel_return": "http://shop.resist.kr/cancel_payment/",
        "custom": "{}".format(order.user)
    }
    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {"form": form}
    return render(request, "payment/payment_paypal.html", context)


@login_required
def get_my_order(request):
    my_orders = Order.objects.filter(user=request.user).prefetch_related('orderdetail_set')
    return render(request, 'my_orders.html', {
        'my_orders': my_orders
    })


# Paypal Payment Checking
@csrf_exempt
def check_payment(sender, **kwargs):
    ipn_obj = sender
    if ipn_obj.payment_status == ST_PP_COMPLETED:
        if ipn_obj.receiver_email != settings.PAYPAL_ID:
            return False
        try:
            order = Order.objects.get(pk=ipn_obj.invoice)
            if ipn_obj.mc_gross == order.total_price:
                order.is_paid = True
                order.save()
                invoice_pk = ipn_obj.invoice
                user = Order.objects.get(pk=invoice_pk).user
                send_mail(
                    user=settings.GMAIL_ID,
                    pwd=settings.GMAIL_PW,
                    recipient=user.email,
                    subject="Payment to SHOPIRK: Via Noir Seoul",
                    body="Hello {},\n"
                         "We've Just got your PAYMENT from PAYPAL.\n"
                         "This is the confirm of your Order's payment.\n"
                         "Your Order Invoice Number: #{}\n"
                         "Total Payment Amount: ${}\n"
                         "Thanks again for your Order.\n"
                         "Sincerely, IRK.".format(
                        user,
                        invoice_pk,
                        ipn_obj.mc_gross
                    ),
                )
                return True
        except:
            return False

@csrf_exempt
def cancel_payment(request):
    pass

@csrf_exempt
def thank_you(request):
    # TODO: Make one more time check for user
    return render(request, 'payment/thankyou.html')

valid_ipn_received.connect(check_payment)


# Staff Order View Page
@staff_member_required
def orderlist(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; ' \
                                      'filename="SHOPIRK_ORDERLIST_{}.csv"'.format(
                                        datetime.now().strftime("%Y%m%d%H%M")
                                      )

    writer = csv.writer(response)
    writer.writerow(['Invoice Number', 'User Email', 'Pay Amount', 'Order Details', 'Custom Orders', 'Shipping Address'])

    qs = Order.objects.filter(is_paid=True).prefetch_related('orderdetail_set')

    for order in qs:
        details = order.orderdetail_set.all()

        order_details = {}
        try:
            for i in details:
                order_details[i.good.name] = i.count
        except TypeError:
            order_details[details.good.name] = details.count


        if order.address != None:
            address = order.address.__str__() + ' // ' + order.additional_address
        else:
            address = ''

        writer.writerow([order.pk, order.user.email, order.total_price, order_details, order.custom_order, address])

    return response


# Korea Bank Check
def korea_bank_payment(request, order_number):
    order = Order.objects.get(pk=order_number)
    currency = requests.get('http://www.floatrates.com/daily/usd.json')
    today_usd_to_krw = int(json.loads(currency)['krw']['rate'] / 10) * 10  # NOT to get 1won but 10won
    if request.method == 'POST':
        pass
    else:
        if order.is_paid:
            return JsonResponse({
                'message': 'This transaction is already paid!'
            })
        data = {
            "amount": order.total_price * today_usd_to_krw,
            "order_number": order_number,
            "today_usd_to_krw": today_usd_to_krw
        }

        return render(request, 'payment/korea_bank_payment.html', data)
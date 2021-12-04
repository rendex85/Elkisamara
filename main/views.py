from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.generic import DetailView, View, CreateView, FormView

from .forms import LoginUserForm, RegisterUserForm, OrderForm
from .models import Category, LatestProducts, Customer, Cart, CartProduct, ChristmasTree, ChristmasTreeChoices
from .mixins import CategoryDetailMixin, CartMixin

# from .forms import OrderForm
from .utils import recalc_cart


class BaseView(CartMixin, View):
    def get(self, request, *args, **kwargs):
        categories = Category.objects.get_categories_for_left_sidebar()
        products = LatestProducts.objects.get_products_for_main_page(

            'christmastree', with_respect_to='christmastree'
        )
        context = {
            'categories': categories,
            'products': products,
            'cart': self.cart
        }

        return render(request, 'html/test.html', context)


class LoginUserView(LoginView):
    form_class = LoginUserForm
    template_name = 'html/login_test.html'


class RegisterUserView(CreateView):
    form_class = RegisterUserForm
    template_name = 'html/register_test.html'
    success_url = reverse_lazy('login')


class ProductDetailView(CartMixin, CategoryDetailMixin, DetailView):
    CT_MODEL_MODEL_CLASS = {
        'christmastree': ChristmasTree,
    }

    def dispatch(self, request, *args, **kwargs):
        self.model = self.CT_MODEL_MODEL_CLASS[kwargs["ct_model"]]
        self.queryset = self.model._base_manager.all()
        return super().dispatch(request, *args, **kwargs)

    context_object_name = 'product'
    template_name = 'PLACEHOLDER_DETAIL.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ct_model'] = self.model._meta.model_name
        context['cart'] = self.cart
        if context['ct_model'] == "christmastree":
            context['tree_choices'] = list(context['product'].choose_height.all())

        return context


class CategoryDetailView(CartMixin, View):
    """
    Фильтрация товаров по категориям.
    Парметры ссылки:
    ct_model - название модели товара, верхний уровень категорий
    slug - второй уровень, подкатегория. Создается в БД и привязывается к продукту

    GET-параметры:
    tree_type - тип дерева (поле product_type в таблице продукты)

    Примеры:
    /category/christmastree/eli/?tree_type=Ель прикольная
    /category/christmastree
    /category/christmastree/pychta
    """

    def get(self, request, *args, **kwargs):
        context = {}
        ct_model, subcategory_slug = kwargs.get('ct_model'), kwargs.get('slug')
        categories = Category.objects.get_categories_for_left_sidebar()
        content_type = ContentType.objects.get(model=ct_model)
        if subcategory_slug:
            products = content_type.model_class().objects.filter(category__slug=subcategory_slug)
            try:
                tree_type = request.GET["tree_type"]
                products = products.filter(product_type=tree_type)
                context['tree_type'] = tree_type
            except KeyError:
                pass
        else:
            products = content_type.model_class().objects.all()
        context['categories'] = categories
        context['cart'] = self.cart

        context['ct_model'] = ct_model
        context['slug'] = subcategory_slug
        context['products'] = list(products)
        return render(request, 'PLACEHOLDER_CATEGORY.html', context)


class AddToCartView(CartMixin, View):
    """
    Добавление в корзину.
    Парметры ссылки:
    slug - slug-поле дерева

    GET-параметры:
    tree_height_id - id размера дерева с ценником

    Пример:
    /add-to-cart/christmastree/elka-from-web/?tree_height_id=2
    """

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get("ct_model"), kwargs.get("slug")
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        cart_product, created = CartProduct.objects.get_or_create(
            user=self.cart.owner,
            cart=self.cart,
            content_type=content_type,
            object_id=product.id,
        )
        if created:
            if ct_model == "christmastree":
                tree_height_id = request.GET["tree_height_id"]
                ChristmasTreeChoices.objects.create(tree=product, cart_product=cart_product,
                                                    tree_height_id=tree_height_id)
            self.cart.products.add(cart_product)
        recalc_cart(self.cart)
        print(self.cart)
        messages.add_message(request, messages.INFO, "Товар успешно добавлен")

        return HttpResponseRedirect("/cart/")


class DeleteFromCartView(CartMixin, View):
    def get(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get("ct_model"), kwargs.get("slug")
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            user=self.cart.owner,
            cart=self.cart,
            content_type=content_type,
            object_id=product.id,
        )
        self.cart.products.remove(cart_product)
        cart_product.delete()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "Товар успешно удален")
        return HttpResponseRedirect("/cart/")


class ChangeQTYView(CartMixin, View):
    def post(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get("ct_model"), kwargs.get("slug")
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            user=self.cart.owner,
            cart=self.cart,
            content_type=content_type,
            object_id=product.id,
        )
        qty = int(request.POST.get("qty"))
        cart_product.qty = qty
        cart_product.save()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "Кол-во успешно изменено")
        # print(self.cart)
        return HttpResponseRedirect('/cart/')


class CartView(CartMixin, View):
    """
    Для получения ct_model для продукта, надо обрпться к iter_elem.content_type.model при итерации по
    Чтобы получить данные о выбранном размере елки надо вызвать get_tree_height_object при итерации по cart.products.all
    """

    def get(self, request, *args, **kwargs):
        categories = Category.objects.get_categories_for_left_sidebar()
        context = {
            'cart': self.cart,
            'categories': categories
        }
        print(context)
        return render(request, 'PLACEHOLDER_CART.html', context)


class CheckoutView(CartMixin, FormView):
    template_name = 'html/checkout_test.html'
    form_class = OrderForm
    success_url = '/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = self.cart
        return context

    def form_valid(self, form):
        customer = Customer.objects.get(user=self.request.user)
        new_order = form.save(commit=False)
        new_order.customer = customer
        new_order.first_name = form.cleaned_data['first_name']
        new_order.last_name = form.cleaned_data['last_name']
        new_order.phone = form.cleaned_data['phone']
        new_order.address = form.cleaned_data['address']
        new_order.buying_type = form.cleaned_data['buying_type']
        # new_order.order_date = form.cleaned_data['order_date']
        new_order.comment = form.cleaned_data['comment']
        self.cart.in_order = True
        self.cart.save()
        new_order.cart = self.cart
        new_order.save()
        customer.orders.add(new_order)
        messages.add_message(self.request, messages.INFO, 'Спасибо за заказ! Менеджер с Вами свяжется')
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form)
        return HttpResponseRedirect('/')


class MakeOrderView(CartMixin, View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = OrderForm(request.POST or None)
        customer = Customer.objects.get(user=request.user)
        if form.is_valid():
            new_order = form.save(commit=False)
            new_order.customer = customer
            new_order.first_name = form.cleaned_data['first_name']
            new_order.last_name = form.cleaned_data['last_name']
            new_order.phone = form.cleaned_data['phone']
            new_order.address = form.cleaned_data['address']
            new_order.buying_type = form.cleaned_data['buying_type']
            # new_order.order_date = form.cleaned_data['order_date']
            new_order.comment = form.cleaned_data['comment']
            new_order.save()
            self.cart.in_order = True
            self.cart.save()
            new_order.cart = self.cart
            new_order.save()
            customer.orders.add(new_order)
            messages.add_message(request, messages.INFO, 'Спасибо за заказ! Менеджер с Вами свяжется')
            return HttpResponseRedirect('/')
        return HttpResponseRedirect('/checkout/')

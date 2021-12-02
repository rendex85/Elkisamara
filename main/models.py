from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

User = get_user_model()


def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


def get_product_url(obj, viewname):
    ct_model = obj.__class__._meta.model_name
    return reverse(viewname, kwargs={'ct_model': ct_model, 'slug': obj.slug})


class LatestProductsManager:

    @staticmethod
    def get_products_for_main_page(*args, **kwargs):
        with_respect_to = kwargs.get('with_respect_to')
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            model_products = ct_model.model_class()._base_manager.all().order_by('-id')[:5]
            products.extend(model_products)
        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists():
                if with_respect_to in args:
                    return sorted(
                        products, key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to), reverse=True
                    )
        return products


class LatestProducts:
    objects = LatestProductsManager()


class CategoryManager(models.Manager):
    CATEGORY_NAME_COUNT_NAME = {
        'Елки': 'christmastree__count',
    }
    PRODUCT_NAMES = {
        'Елки': 'christmastree',
    }

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_left_sidebar(self):
        data = []
        for product_key, product_value in self.PRODUCT_NAMES.items():
            category_dict = {"category_name": product_key, "category_slug": product_value, "subcategories": []}

            content_type = ContentType.objects.get(model=product_value)
            subcategories = content_type.model_class().objects.values("category").annotate(dcount=Count('category'))

            for subcategory in subcategories:
                subcategory_object = Category.objects.get(pk=subcategory["category"])
                subcategory_dict = {"subcategory_name": subcategory_object.name,
                                    "subcategory_slug": subcategory_object.slug,
                                    "types": []}

                types = content_type.model_class().objects.values("product_type").filter(
                    category_id=subcategory["category"]).annotate(
                    dcount=Count('product_type'))
                for type_product in types:
                    subcategory_dict["types"].append({"product_type_name": type_product["product_type"]})
                category_dict["subcategories"].append(subcategory_dict)
            data.append(category_dict)
        return data


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Имя категории')
    slug = models.SlugField(unique=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})

    class Meta:
        verbose_name = 'Категория товара'
        verbose_name_plural = 'Категории товаров'


class Product(models.Model):
    class Meta:
        abstract = True

    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='Наименование')
    slug = models.SlugField(unique=True)
    # Надо заменить дефолт=нулл на плейсхолдер для товаров без изображения
    image = models.ImageField(verbose_name='Изображение', upload_to="products", null=True, blank=True, default=None)
    description = models.TextField(verbose_name='Описание', null=True, blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Цена, руб')
    product_type = models.CharField(max_length=255, verbose_name='Тип продукта', null=True, blank=True)

    def image_tag(self):
        resize_img = 1
        if self.image.height > self.image.width:
            resize_img = self.image.height / 400
        else:
            resize_img = self.image.width / 400
        return mark_safe(
            f'<img src={self.image.url} width="{self.image.width / resize_img}" height="{self.image.height / resize_img}" />')

    image_tag.short_description = 'Изображение товара'

    def __str__(self):
        return self.title

    def get_model_name(self):
        return self.__class__.__name__.lower()


class ChristmasTreeHeight(models.Model):
    tree_height = models.CharField(max_length=255, verbose_name='Рост елки, м', null=True, blank=True)
    tree_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Цена, руб')

    def __str__(self):
        return f"Рост: {self.tree_height} м., цена: {self.tree_price} руб."

    class Meta:
        verbose_name = 'Размеры Ёлок'
        verbose_name_plural = 'Размеры Ёлок'


class ChristmasTree(Product):
    choose_height = models.ManyToManyField(ChristmasTreeHeight, max_length=255, verbose_name='Рост елки, м', null=True,
                                           blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Цена, руб', null=True, blank=True)
    product_type = models.CharField(max_length=255, verbose_name='Тип дерева', null=True, blank=True)
    # weight = models.IntegerField(verbose_name='Вес, кг', null=True, blank=True)
    from_place = models.CharField(max_length=512, verbose_name='Откуда привезена', null=True, blank=True)
    image = models.ImageField(verbose_name='Изображение', upload_to="products/tree", null=True, blank=True)

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')

    def get_prices(self):
        return get_product_url(self, 'product_detail')

    class Meta:
        verbose_name = 'Елка'
        verbose_name_plural = 'Елки'


"""
class Smartphone(Product):

    diagonal = models.CharField(max_length=255, verbose_name='Диагональ')
    display_type = models.CharField(max_length=255, verbose_name='Тип дисплея')
    resolution = models.CharField(max_length=255, verbose_name='Разрешение экрана')
    accum_volume = models.CharField(max_length=255, verbose_name='Объем батареи')
    ram = models.CharField(max_length=255, verbose_name='Оперативная память')
    sd = models.BooleanField(default=True, verbose_name='Наличие SD карты')
    sd_volume_max = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='Максимальный объем встраивамой памяти'
    )
    main_cam_mp = models.CharField(max_length=255, verbose_name='Главная камера')
    frontal_cam_mp = models.CharField(max_length=255, verbose_name='Фронтальная камера')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')

"""


class CartProduct(models.Model):
    user = models.ForeignKey('Customer', verbose_name='Покупатель', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', verbose_name='Корзина', on_delete=models.CASCADE, related_name='related_products',
                             null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Общая цена', null=True, blank=True)

    def get_tree_height_object(self):
        try:
            return ChristmasTreeChoices.objects.get(cart_product=self)
        except ChristmasTreeChoices.DoesNotExist:
            return None

    def __str__(self):
        return f"{self.content_object.category}: {self.content_object.title} (id: {self.object_id}, кол-во: {self.qty})"

    def save(self, *args, **kwargs):
        if not self.content_type == ContentType.objects.get(model="christmastree"):
            self.final_price = self.qty * self.content_object.price
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Продукт в корзине'
        verbose_name_plural = 'Продукты в корзине'


class ChristmasTreeChoices(models.Model):
    tree = models.ForeignKey(ChristmasTree, verbose_name="Елка", on_delete=models.CASCADE)
    cart_product = models.ForeignKey(CartProduct, verbose_name="Елка в корзине", on_delete=models.CASCADE,
                                     related_name="tree_in_cart")
    tree_height = models.ForeignKey(ChristmasTreeHeight, verbose_name="Рост Елки", on_delete=models.CASCADE, )

    def save(self, *args, **kwargs):
        self.cart_product.final_price = self.cart_product.qty * self.tree_height.tree_price
        self.cart_product.save()
        super().save(*args, **kwargs)


class Cart(models.Model):
    owner = models.ForeignKey('Customer', null=True, verbose_name='Владелец', on_delete=models.CASCADE)
    products = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart',
                                      verbose_name='Товары в корзине')
    total_products = models.PositiveIntegerField(default=0, verbose_name="Всего товара, шт")
    final_price = models.DecimalField(max_digits=9, default=0, decimal_places=2, verbose_name='Общая цена, руб')
    in_order = models.BooleanField(default=False, verbose_name="Оформлен ли заказ?")
    for_anonymous_user = models.BooleanField(default=False, verbose_name="Зарегистрован ли пользователь?")

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Корзина  пользователя'
        verbose_name_plural = 'Корзины пользователя'


class Customer(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='Номер телефона', null=True, blank=True)
    address = models.CharField(max_length=255, verbose_name='Адрес', null=True, blank=True)
    orders = models.ManyToManyField('Order', verbose_name='Заказы покупателя', related_name='related_order', null=True,
                                    blank=True)

    def __str__(self):
        return "Покупатель: {} {}".format(self.user.first_name, self.user.last_name)

    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'


class Order(models.Model):
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_COMPLETED = 'completed'

    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY = 'delivery'

    STATUS_CHOICES = (
        (STATUS_NEW, 'Новый заказ'),
        (STATUS_IN_PROGRESS, 'Заказ в обработке'),
        (STATUS_READY, 'Заказ готов'),
        (STATUS_COMPLETED, 'Заказ выполнен')
    )

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'Самовывоз'),
        (BUYING_TYPE_DELIVERY, 'Доставка')
    )

    customer = models.ForeignKey(Customer, verbose_name='Покупатель', related_name='related_orders',
                                 on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, verbose_name='Имя', null=True, blank=True)
    last_name = models.CharField(max_length=255, verbose_name='Фамилия', null=True, blank=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон', null=True, blank=True, default=None)
    cart = models.ForeignKey(Cart, verbose_name='Корзина', on_delete=models.CASCADE)
    address = models.CharField(max_length=1024, verbose_name='Адрес', null=True, blank=True)
    status = models.CharField(
        max_length=100,
        verbose_name='Статус заказ',
        choices=STATUS_CHOICES,
        default=STATUS_NEW
    )
    buying_type = models.CharField(
        max_length=100,
        verbose_name='Тип заказа',
        choices=BUYING_TYPE_CHOICES,
        default=BUYING_TYPE_SELF
    )
    comment = models.TextField(verbose_name='Комментарий к заказу', null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, verbose_name='Дата создания заказа')
    order_date = models.DateField(verbose_name='Дата получения заказа', default=timezone.now)
    order_content_description = models.TextField(verbose_name='Описания составляющих заказа', null=True, blank=True)

    def __str__(self):
        return f"Заказ номер: {self.id}, дата: {self.created_at.date()},  {self.customer} "

    def save(self, *args, **kwargs):
        # Если имя, фамилия и телефон в заказе пустые - указываем данные самого пользователя
        if not (self.first_name or self.last_name or self.phone):
            self.first_name = self.customer.user.first_name
            self.first_name = self.customer.user.last_name
            self.first_name = self.customer.phone
        # Если не указан адрес, используем адрес пользователя
        if not self.address:
            self.address = self.customer.address

        # Составляем описание заказа
        description_string = f"Заказ №{self.id}\nОбщая сумма заказа: {self.cart.final_price} руб., " \
                             f"общее число товаров: {self.cart.total_products} шт.\n\n" \
                             f"Товары:\n"

        for product in self.cart.products.all():
            description_string += f"Наименование: {product.content_object.title}. Количество: {product.qty} шт., " \
                                  f"суммарная стоимость: {product.final_price} руб.\n"
        self.order_content_description = description_string
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

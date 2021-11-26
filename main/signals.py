from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from main.models import Cart


@receiver(m2m_changed , sender=Cart.products.through)
def save_post(sender, instance, **kwargs):
    """
    Автоматически считает общую стоимость корзины и количество продуктов
    """
    cart_products = instance.products.all()
    print(cart_products)
    instance.final_price = sum(product.final_price for product in cart_products)
    instance.total_products = sum(product.qty for product in cart_products)
    instance.save()

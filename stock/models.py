from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True, null=True)
    stock = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)

    def update_average_cost(self, added_quantity, added_cost):
        total_cost = (self.stock * self.average_cost) + \
            (added_quantity * added_cost)
        total_quantity = self.stock + added_quantity
        self.average_cost = total_cost / total_quantity

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', "category__name"]


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images",
    )
    image = models.ImageField(upload_to="product_images/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Imagen de {self.product}"


class PurchaseInvoice(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(default=timezone.now)
    supplier = models.CharField(max_length=200, default="Aliexpress")

    def get_total(self):
        return sum(item.get_total() for item in self.items.all())

    def __str__(self):
        return f"Purchase Invoice #{self.id} - {self.supplier}"

    class Meta:
        ordering = ['-date']


class Purchase(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    invoice = models.ForeignKey(
        PurchaseInvoice, on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def get_total(self):
        return self.quantity * self.cost

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            old = Purchase.objects.get(pk=self.pk)
            if old.product_id == self.product_id and old.quantity == self.quantity \
                    and old.cost == self.cost:
                super().save(*args, **kwargs)
                return
            # Revertir el efecto en el producto viejo
            old_prod = old.product
            if old_prod.stock - old.quantity > 0:
                old_prod.average_cost = (
                    (old_prod.stock * old_prod.average_cost
                     - old.quantity * old.cost) / (old_prod.stock - old.quantity)
                )
            else:
                old_prod.average_cost = 0
            old_prod.stock -= old.quantity
            old_prod.save()
            # Si el producto cambió, descuento la nueva cantidad debe ir al nuevo
            if old.product_id != self.product_id:
                new_prod = self.product
                new_prod.update_average_cost(self.quantity, self.cost)
                new_prod.stock += self.quantity
                new_prod.save()
            else:
                # Mismo producto: aplicar delta sobre old_prod ya revertido
                old_prod.update_average_cost(self.quantity, self.cost)
                old_prod.stock += self.quantity
                old_prod.save()
                self.product = old_prod

        else:
            self.product.update_average_cost(self.quantity, self.cost)
            self.product.stock += self.quantity
            self.product.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        product = self.product
        if product.stock - self.quantity > 0:
            # Revert average cost
            total_value = (product.stock * product.average_cost) - \
                (self.quantity * self.cost)
            new_quantity = product.stock - self.quantity
            product.average_cost = total_value / new_quantity
        else:
            product.average_cost = 0
        product.stock -= self.quantity
        self.product.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Purchase #{self.id} - {self.quantity} x {self.product}"


class SaleInvoice(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(default=timezone.now)
    customer = models.CharField(max_length=200, default="Generic")

    def get_total(self):
        return sum(item.get_total() for item in self.items.all())

    def __str__(self):
        return f"Sale Invoice #{self.id} - {self.customer}"

    class Meta:
        ordering = ['-date']


class Sale(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    invoice = models.ForeignKey(
        SaleInvoice, on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total(self):
        return self.quantity * self.price

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.pk:
            old = Sale.objects.get(pk=self.pk)
            if old.product_id == self.product_id and old.quantity == self.quantity:
                super().save(*args, **kwargs)
                return
            # Revertir el efecto en el producto viejo
            old_prod = old.product
            if old.product_id != self.product_id:
                old_prod.stock += old.quantity
                old_prod.save()
                # Descontar del nuevo producto
                new_prod = self.product
                new_prod.stock -= self.quantity
                new_prod.save()
                self.price = new_prod.price
                self.cost = new_prod.average_cost
            else:
                # Mismo producto: aplicar delta neto sobre stock
                old_prod.stock += old.quantity - self.quantity
                old_prod.save()
                self.price = old_prod.price
                self.cost = old_prod.average_cost
                self.product = old_prod
        else:
            self.product.stock -= self.quantity
            self.price = self.product.price
            self.cost = self.product.average_cost
            self.product.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.product.stock += self.quantity
        self.product.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Sale #{self.id} - {self.quantity} x {self.product}"


class Expense(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(default=timezone.now)
    category = models.ForeignKey(
        ExpenseCategory, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    description = models.TextField(blank=True, null=True)

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"C$ {self.amount} - {self.description}"

    class Meta:
        ordering = ['-created_at']
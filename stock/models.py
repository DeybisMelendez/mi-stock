from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
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


class Purchase(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateTimeField(default=timezone.now)
    supplier = models.CharField(max_length=200, default="Aliexpress")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def get_total(self):
        return self.quantity * self.cost

    def save(self, *args, **kwargs):
        if not self.pk:
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


class Sale(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateTimeField(default=timezone.now)
    customer = models.CharField(max_length=200, default="Generic")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total(self):
        return self.quantity * self.price

    def save(self, *args, **kwargs):
        if not self.pk:
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

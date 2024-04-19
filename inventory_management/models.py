from django.db import models
from django.forms import ValidationError
from django.urls import reverse
from django.utils.text import slugify
import uuid 

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Nome da Categoria", max_length=100)
    slug = models.SlugField("Slug", max_length=100, blank=True, null=True, editable=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)

    @property
    def quantity(self):
        return self.product_set.count()
    quantity.fget.short_description = "Quantidade"

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categorias"
        verbose_name = "Categoria"

    def get_absolute_url(self):
        return reverse('inventory_management:category_items', kwargs={'slug': self.slug})


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey('inventory_management.Category', on_delete=models.CASCADE, verbose_name="Categoria")
    name = models.CharField("Nome do Produto", max_length=100)
    description = models.TextField("Descrição")
    price = models.DecimalField("Preço", max_digits=10, decimal_places=2)
    image = models.ImageField("Imagem", upload_to='product_images', blank=True, null=True)
    slug = models.SlugField("Slug", max_length=100, blank=True, null=True, editable=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Product, self).save(*args, **kwargs)

    @property
    def quantity(self):
        return self.productunit_set.count()

    quantity.fget.short_description = "Quantidade"

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Produtos"
        verbose_name = "Produto"
    
    def get_absolute_url(self):
        return reverse('inventory_management:product_detail', kwargs={'category_slug':self.category.slug, 'slug': self.slug})


class ProductUnit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey("Product", on_delete=models.CASCADE, verbose_name="Produto")
    location = models.ForeignKey('inventory_management.Room', on_delete=models.CASCADE, verbose_name="Localização")
    purchase_date = models.DateField("Data de Compra", null=True, blank=True)
    quantity = models.IntegerField("Quantidade", default=1)
    write_off = models.BooleanField("Baixado?", default=False)
    modified = models.DateTimeField("Modificado", auto_now=True)
    slug = models.SlugField("Slug", max_length=100, blank=True, null=True, editable=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.id)
        super(ProductUnit, self).save(*args, **kwargs)
        for i in range(1, self.quantity):
            ProductUnit.objects.create(product=self.product, location=self.location, purchase_date=self.purchase_date,)

        self.__class__.objects.filter(id=self.id).update(quantity=1)


    def clean(self):
        if self.quantity < 1:
            raise ValidationError("A quantidade deve ser maior que 0.")
        
    def __str__(self):
        return f'{self.product.name} - {self.slug}'

    class Meta:
        verbose_name_plural = "Unidades de Produto"
        verbose_name = "Unidade de Produto"
        ordering = ['write_off', 'purchase_date', 'product']

    def get_absolute_url(self):
        return reverse('inventory_management:product_unit_detail', kwargs={'category_slug':self.product.category.slug, 'product_slug':self.product.slug, 'slug': self.slug})


class StockTransfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_unit = models.ForeignKey(ProductUnit, on_delete=models.CASCADE, verbose_name="Unidade de Produto")
    origin = models.ForeignKey('inventory_management.Room', on_delete=models.CASCADE, related_name="origin", verbose_name="Origem")
    destination = models.ForeignKey('inventory_management.Room', on_delete=models.CASCADE, related_name="destination", verbose_name="Destino")
    transfer_date = models.DateField("Data da Transferência")
    observations = models.TextField("Observações", blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.origin == self.destination:
            raise ValidationError("Origem e destino não podem ser iguais.")
        if self.product_unit.write_off:
            raise ValidationError("A unidade de produto foi baixada.")
        if self.product_unit.location != self.origin:
            raise ValidationError("A unidade de produto não está na origem.")
        
        self.product_unit.location = self.destination
        self.product_unit.save()
        super(StockTransfer, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_unit.product.name} - {self.origin.building} (sala {self.origin}) -> {self.destination.building} (sala {self.destination})"

    class Meta:
        verbose_name_plural = "Transferências de Estoque"
        verbose_name = "Transferência de Estoque"

    def get_absolute_url(self):
        return reverse('inventory_management:product_unit_detail', kwargs={'category_slug':self.product_unit.product.category.slug, 'product_slug':self.product_unit.product.slug, 'slug': self.product_unit.slug})


class Building(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Nome do Prédio", max_length=100)
    cep = models.CharField("CEP", max_length=8)
    street = models.CharField("Rua", max_length=100)
    number = models.CharField("Número", max_length=10)
    complement = models.CharField("Complemento", max_length=100)
    neighborhood = models.CharField("Bairro", max_length=100)
    city = models.CharField("Cidade", max_length=100)
    state = models.CharField("Estado (UF)", max_length=2)
    slug = models.SlugField("Slug", max_length=100, blank=True, null=True, editable=False)

    def full_address(self):
        return f"{self.street}, {self.number} - {self.neighborhood}, {self.city} - {self.state}, {self.cep}"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.id)
        super(Building, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Prédios"
        verbose_name = "Prédio"


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Nome da Sala", max_length=100)
    hall = models.CharField("Corredor", max_length=100, default="N/A")
    shelf = models.CharField("Prateleira", max_length=100, default="N/A")
    building = models.ForeignKey(Building, on_delete=models.CASCADE, verbose_name="Prédio")
    slug = models.SlugField("Slug", max_length=100, blank=True, null=True, editable=False)

    def full_address(self):
        return f"{self.building.street}, {self.building.number} - {self.building.neighborhood}, {self.building.city} - {self.building.state}, {self.building.cep} - Sala {self.name} - Corredor {self.hall} - Prateleira {self.shelf}"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.id)
        super(Room, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.building.name} - Sala {self.name} - Corredor {self.hall} - Prateleira {self.shelf}'

    class Meta:
        verbose_name_plural = "Salas"
        verbose_name = "Sala"
        ordering = ['building', 'name']

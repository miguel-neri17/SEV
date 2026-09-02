from django.db import models
from django.utils import timezone

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

    def __str__(self):
        return self.nome

class Fornecedor(models.Model):
    nome = models.CharField(max_length=150)
    telefone = models.CharField(max_length=30, blank=True)
    email = models.CharField(max_length=150, blank=True)
    cnpj = models.CharField(max_length=30, blank=True)
    especialidade = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'

    def __str__(self):
        return self.nome

class Produto(models.Model):
    UNIDADES = [
        ('unidade', 'Unidade'), ('caixa', 'Caixa'), ('pacote', 'Pacote'),
        ('kg', 'Kg'), ('litro', 'Litro')
    ]
    nome = models.CharField(max_length=150)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='produtos')
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT, related_name='produtos')
    quantidade_estoque = models.PositiveIntegerField(default=0)
    estoque_minimo = models.PositiveIntegerField(default=5)
    preco_compra = models.DecimalField(max_digits=10, decimal_places=2)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2)
    data_cadastro = models.DateField(default=timezone.localdate)
    data_ultima_entrada = models.DateField(null=True, blank=True)
    quantidade_entrada = models.PositiveIntegerField(default=0)
    unidade_medida = models.CharField(max_length=20, choices=UNIDADES, default='unidade')
    localizacao_estoque = models.CharField(max_length=100, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'

    def __str__(self):
        return self.nome

    @property
    def estoque_baixo(self):
        return self.quantidade_estoque <= self.estoque_minimo

    @property
    def margem_unitaria(self):
        return self.preco_venda - self.preco_compra

class Venda(models.Model):
    FORMAS = [
        ('Dinheiro', 'Dinheiro'), ('Cartão de Débito', 'Cartão de Débito'),
        ('Cartão de Crédito', 'Cartão de Crédito'), ('Pix', 'Pix')
    ]
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name='vendas')
    data_venda = models.DateField(default=timezone.localdate)
    quantidade_vendida = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    forma_pagamento = models.CharField(max_length=30, choices=FORMAS)
    vendedor = models.CharField(max_length=100)
    cliente = models.CharField(max_length=100, blank=True)
    nota_cliente = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)

    class Meta:
        ordering = ['-data_venda', '-id']
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'

    def __str__(self):
        return f'Venda #{self.pk} - {self.produto}'

    @property
    def valor_total(self):
        return self.preco_unitario * self.quantidade_vendida

    @property
    def valor_final(self):
        return self.valor_total - self.desconto

    @property
    def lucro_venda(self):
        return (self.preco_unitario - self.produto.preco_compra) * self.quantidade_vendida - self.desconto

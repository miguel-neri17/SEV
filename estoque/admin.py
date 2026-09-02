from django.contrib import admin
from .models import Categoria, Fornecedor, Produto, Venda

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')
    search_fields = ('nome',)

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'telefone', 'email', 'cnpj', 'especialidade')
    search_fields = ('nome', 'email', 'cnpj', 'especialidade')

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'categoria', 'quantidade_estoque', 'estoque_minimo', 'preco_venda', 'ativo')
    list_filter = ('categoria', 'ativo')
    search_fields = ('nome', 'fornecedor__nome')

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'produto', 'data_venda', 'quantidade_vendida', 'preco_unitario', 'forma_pagamento', 'vendedor')
    list_filter = ('data_venda', 'forma_pagamento')
    search_fields = ('produto__nome', 'vendedor', 'cliente')

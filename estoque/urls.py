from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Autenticação com as telas do próprio SEV, fora do /admin/.
    path('entrar/', auth_views.LoginView.as_view(
        template_name='estoque/login.html',
        redirect_authenticated_user=True,
    ), name='login'),
    path('sair/', auth_views.LogoutView.as_view(), name='logout'),
    path('registrar/', views.registrar, name='registrar'),

    # Fluxo equivalente ao exemplo dos PDFs (/membros/), adaptado ao tema SEV.
    path('membros/', views.introducao_pdf, name='listar_membros'),
    path('membros/criar/', views.produto_criar, name='criar_membro'),
    path('membros/atualizar/<int:pk>/', views.produto_editar, name='atualizar_membro'),
    path('membros/deletar/<int:pk>/', views.produto_excluir, name='deletar_membro'),

    path('', views.dashboard, name='dashboard'),

    path('produtos/', views.produto_lista, name='produto_lista'),
    path('produtos/novo/', views.produto_criar, name='produto_criar'),
    path('produtos/<int:pk>/editar/', views.produto_editar, name='produto_editar'),
    path('produtos/<int:pk>/excluir/', views.produto_excluir, name='produto_excluir'),

    path('categorias/', views.categoria_lista, name='categoria_lista'),
    path('categorias/novo/', views.categoria_criar, name='categoria_criar'),
    path('categorias/<int:pk>/editar/', views.categoria_editar, name='categoria_editar'),
    path('categorias/<int:pk>/excluir/', views.categoria_excluir, name='categoria_excluir'),

    path('fornecedores/', views.fornecedor_lista, name='fornecedor_lista'),
    path('fornecedores/novo/', views.fornecedor_criar, name='fornecedor_criar'),
    path('fornecedores/<int:pk>/editar/', views.fornecedor_editar, name='fornecedor_editar'),
    path('fornecedores/<int:pk>/excluir/', views.fornecedor_excluir, name='fornecedor_excluir'),

    path('vendas/', views.venda_lista, name='venda_lista'),
    path('vendas/nova/', views.venda_criar, name='venda_criar'),
    path('vendas/<int:pk>/excluir/', views.venda_excluir, name='venda_excluir'),

    path('relatorios/', views.relatorios, name='relatorios'),
]

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import (
    Count, DecimalField, ExpressionWrapper, F, ProtectedError, Sum,
)
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    CategoriaForm, FornecedorForm, ProdutoForm, RegistroForm, VendaForm,
)
from .models import Categoria, Fornecedor, Produto, Venda

DINHEIRO = DecimalField(max_digits=12, decimal_places=2)


# ---------------------------------------------------------------- cadastro

def registrar(request):
    """Cria um novo usuário e já o deixa logado.

    Não exige login: é a porta de entrada de quem ainda não tem conta.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        messages.success(request, f'Conta criada! Bem-vindo(a), {usuario.username}.')
        return redirect('dashboard')
    return render(request, 'estoque/registro.html', {'form': form})

# valor_final = preço unitário * quantidade - desconto
VALOR_FINAL = ExpressionWrapper(
    F('preco_unitario') * F('quantidade_vendida') - F('desconto'),
    output_field=DINHEIRO,
)

# lucro = (preço de venda - preço de compra) * quantidade - desconto
LUCRO = ExpressionWrapper(
    (F('preco_unitario') - F('produto__preco_compra')) * F('quantidade_vendida') - F('desconto'),
    output_field=DINHEIRO,
)


def _totais_vendas(vendas):
    """Faturamento e lucro calculados no banco, em uma única consulta."""
    totais = vendas.aggregate(faturamento=Sum(VALOR_FINAL), lucro=Sum(LUCRO))
    return (totais['faturamento'] or Decimal('0'), totais['lucro'] or Decimal('0'))


def _dados_graficos():
    """Monta os dados dos gráficos com um número fixo de consultas."""
    categorias = list(Categoria.objects.all())
    produtos = list(Produto.objects.filter(ativo=True))

    estoque_por_categoria = {
        linha['categoria_id']: linha['total'] or 0
        for linha in Produto.objects.filter(ativo=True)
        .values('categoria_id')
        .annotate(total=Sum('quantidade_estoque'))
    }
    vendas_por_categoria = {
        linha['produto__categoria_id']: linha['total'] or 0
        for linha in Venda.objects.values('produto__categoria_id')
        .annotate(total=Sum('quantidade_vendida'))
    }
    faturamento_por_categoria = {
        linha['produto__categoria_id']: float(linha['total'] or 0)
        for linha in Venda.objects.values('produto__categoria_id')
        .annotate(total=Sum(VALOR_FINAL))
    }
    faturamento_por_produto = {
        linha['produto_id']: float(linha['total'] or 0)
        for linha in Venda.objects.values('produto_id').annotate(total=Sum(VALOR_FINAL))
    }

    pagamentos = (
        Venda.objects.values('forma_pagamento')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    return {
        'categorias': {
            'labels': [c.nome for c in categorias],
            'estoque': [estoque_por_categoria.get(c.id, 0) for c in categorias],
            'vendas': [vendas_por_categoria.get(c.id, 0) for c in categorias],
            'faturamento': [faturamento_por_categoria.get(c.id, 0.0) for c in categorias],
        },
        'produtos': {
            'labels': [p.nome for p in produtos],
            'faturamento': [faturamento_por_produto.get(p.id, 0.0) for p in produtos],
        },
        'pagamentos': {
            'labels': [p['forma_pagamento'] for p in pagamentos],
            'valores': [p['total'] for p in pagamentos],
        },
    }


# ---------------------------------------------------------------- dashboard

@login_required
def dashboard(request):
    produtos = Produto.objects.filter(ativo=True)
    vendas = Venda.objects.select_related('produto')
    faturamento, lucro = _totais_vendas(vendas)

    context = {
        'total_produtos': produtos.count(),
        'total_estoque': produtos.aggregate(total=Sum('quantidade_estoque'))['total'] or 0,
        'total_vendas': vendas.count(),
        'faturamento': faturamento,
        'lucro': lucro,
        'baixo_estoque': produtos.filter(
            quantidade_estoque__lte=F('estoque_minimo')
        ).order_by('quantidade_estoque'),
        'mais_vendidos': (
            vendas.values('produto__nome')
            .annotate(total=Sum('quantidade_vendida'))
            .order_by('-total')[:5]
        ),
        'dados_graficos': _dados_graficos(),
    }
    return render(request, 'estoque/dashboard.html', context)


# ---------------------------------------------------------------- produtos

@login_required
def produto_lista(request):
    produtos = Produto.objects.select_related('categoria', 'fornecedor').all()
    busca = request.GET.get('q', '').strip()
    if busca:
        produtos = produtos.filter(nome__icontains=busca)
    return render(request, 'estoque/produto_lista.html', {'produtos': produtos, 'busca': busca})


@login_required
def produto_criar(request):
    form = ProdutoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Produto cadastrado com sucesso!')
        return redirect('produto_lista')
    return render(request, 'estoque/form.html', {
        'form': form, 'titulo': 'Cadastrar produto', 'voltar': 'produto_lista',
    })


@login_required
def produto_editar(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    form = ProdutoForm(request.POST or None, instance=produto)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Produto atualizado com sucesso!')
        return redirect('produto_lista')
    return render(request, 'estoque/form.html', {
        'form': form, 'titulo': 'Editar produto', 'voltar': 'produto_lista',
    })


@login_required
def produto_excluir(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == 'POST':
        try:
            produto.delete()
            messages.success(request, 'Produto excluído com sucesso!')
        except ProtectedError:
            messages.error(
                request,
                'Não é possível excluir um produto que já possui vendas registradas. '
                'Desmarque a opção "Produto ativo" para tirá-lo de circulação.',
            )
        return redirect('produto_lista')
    return render(request, 'estoque/confirmar_exclusao.html', {
        'objeto': produto, 'voltar': 'produto_lista',
    })


# ---------------------------------------------------------------- categorias

@login_required
def categoria_lista(request):
    return render(request, 'estoque/categoria_lista.html', {
        'categorias': Categoria.objects.all(),
    })


@login_required
def categoria_criar(request):
    form = CategoriaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Categoria cadastrada!')
        return redirect('categoria_lista')
    return render(request, 'estoque/form.html', {
        'form': form, 'titulo': 'Cadastrar categoria', 'voltar': 'categoria_lista',
    })


@login_required
def categoria_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    form = CategoriaForm(request.POST or None, instance=categoria)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Categoria atualizada!')
        return redirect('categoria_lista')
    return render(request, 'estoque/form.html', {
        'form': form, 'titulo': 'Editar categoria', 'voltar': 'categoria_lista',
    })


@login_required
def categoria_excluir(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        try:
            categoria.delete()
            messages.success(request, 'Categoria excluída!')
        except ProtectedError:
            messages.error(request, 'Não é possível excluir uma categoria que possui produtos.')
        return redirect('categoria_lista')
    return render(request, 'estoque/confirmar_exclusao.html', {
        'objeto': categoria, 'voltar': 'categoria_lista',
    })


# ---------------------------------------------------------------- fornecedores

@login_required
def fornecedor_lista(request):
    return render(request, 'estoque/fornecedor_lista.html', {
        'fornecedores': Fornecedor.objects.all(),
    })


@login_required
def fornecedor_criar(request):
    form = FornecedorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Fornecedor cadastrado!')
        return redirect('fornecedor_lista')
    return render(request, 'estoque/form.html', {
        'form': form, 'titulo': 'Cadastrar fornecedor', 'voltar': 'fornecedor_lista',
    })


@login_required
def fornecedor_editar(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    form = FornecedorForm(request.POST or None, instance=fornecedor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Fornecedor atualizado!')
        return redirect('fornecedor_lista')
    return render(request, 'estoque/form.html', {
        'form': form, 'titulo': 'Editar fornecedor', 'voltar': 'fornecedor_lista',
    })


@login_required
def fornecedor_excluir(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    if request.method == 'POST':
        try:
            fornecedor.delete()
            messages.success(request, 'Fornecedor excluído!')
        except ProtectedError:
            messages.error(request, 'Não é possível excluir um fornecedor que possui produtos.')
        return redirect('fornecedor_lista')
    return render(request, 'estoque/confirmar_exclusao.html', {
        'objeto': fornecedor, 'voltar': 'fornecedor_lista',
    })


# ---------------------------------------------------------------- vendas

@login_required
def venda_lista(request):
    return render(request, 'estoque/venda_lista.html', {
        'vendas': Venda.objects.select_related('produto'),
    })


@login_required
def venda_criar(request):
    form = VendaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            venda = form.save()
            # F() evita perder a baixa se duas vendas forem salvas ao mesmo tempo.
            Produto.objects.filter(pk=venda.produto_id).update(
                quantidade_estoque=F('quantidade_estoque') - venda.quantidade_vendida
            )
        messages.success(request, 'Venda registrada e estoque atualizado!')
        return redirect('venda_lista')
    return render(request, 'estoque/form.html', {
        'form': form, 'titulo': 'Registrar venda', 'voltar': 'venda_lista',
    })


@login_required
def venda_excluir(request, pk):
    venda = get_object_or_404(Venda.objects.select_related('produto'), pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            # Devolve as unidades ao estoque antes de apagar a venda.
            Produto.objects.filter(pk=venda.produto_id).update(
                quantidade_estoque=F('quantidade_estoque') + venda.quantidade_vendida
            )
            venda.delete()
        messages.success(request, 'Venda excluída e estoque devolvido!')
        return redirect('venda_lista')
    return render(request, 'estoque/confirmar_exclusao.html', {
        'objeto': venda, 'voltar': 'venda_lista',
    })


# ---------------------------------------------------------------- relatórios

@login_required
def relatorios(request):
    vendas = Venda.objects.select_related('produto')
    faturamento, lucro = _totais_vendas(vendas)
    return render(request, 'estoque/relatorios.html', {
        'por_produto': (
            vendas.values('produto__nome')
            .annotate(qtd=Sum('quantidade_vendida'))
            .order_by('-qtd')
        ),
        'por_forma': (
            vendas.values('forma_pagamento')
            .annotate(qtd=Count('id'))
            .order_by('-qtd')
        ),
        'baixo': Produto.objects.filter(
            ativo=True, quantidade_estoque__lte=F('estoque_minimo')
        ).order_by('quantidade_estoque'),
        'faturamento': faturamento,
        'lucro': lucro,
        'dados_graficos': _dados_graficos(),
    })


@login_required
def introducao_pdf(request):
    produtos = Produto.objects.select_related('categoria', 'fornecedor').all()
    return render(request, 'estoque/meuprimeiro.html', {'produtos': produtos})

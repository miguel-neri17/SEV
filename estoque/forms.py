from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Categoria, Fornecedor, Produto, Venda


class RegistroForm(UserCreationForm):
    """Cadastro de um novo usuário do SEV.

    Cada cadastro cria mais um usuário na tabela de usuários: os que já
    existem (inclusive o admin) continuam valendo normalmente.
    """

    class Meta:
        model = User
        fields = ['username']
        labels = {'username': 'Usuário'}
        help_texts = {'username': 'Até 150 caracteres. Letras, números e @ . + - _'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Senha'
        self.fields['password2'].label = 'Confirme a senha'
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = 'Digite a mesma senha de novo, para conferência.'

    def clean_username(self):
        nome = self.cleaned_data['username']
        if User.objects.filter(username__iexact=nome).exists():
            raise forms.ValidationError('Já existe um usuário com esse nome. Escolha outro.')
        return nome


class DateInput(forms.DateInput):
    """Campo de data nativo do navegador.

    O format='%Y-%m-%d' é obrigatório: o input type="date" só aceita ISO,
    enquanto o locale pt-br renderizaria 25/10/2026 e o campo ficaria vazio.
    """
    input_type = 'date'

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format='%Y-%m-%d')


def _traduzir_opcao_vazia(form, textos=None):
    """Troca o rótulo em inglês "- Select an option -" por português."""
    textos = textos or {}
    for nome, campo in form.fields.items():
        padrao = textos.get(nome, 'Selecione uma opção')
        if isinstance(campo, forms.ModelChoiceField):
            campo.empty_label = padrao
        elif getattr(campo, 'choices', None):
            opcoes = list(campo.choices)
            if opcoes and opcoes[0][0] in ('', None):
                campo.choices = [('', padrao)] + opcoes[1:]


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'descricao']
        labels = {
            'nome': 'Nome',
            'descricao': 'Descrição',
        }


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'telefone', 'email', 'cnpj', 'especialidade']
        labels = {
            'nome': 'Nome',
            'telefone': 'Telefone',
            'email': 'E-mail',
            'cnpj': 'CNPJ',
            'especialidade': 'Especialidade',
        }


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            'nome', 'categoria', 'fornecedor', 'quantidade_estoque', 'estoque_minimo',
            'preco_compra', 'preco_venda', 'data_cadastro', 'data_ultima_entrada',
            'quantidade_entrada', 'unidade_medida', 'localizacao_estoque', 'ativo',
        ]
        labels = {
            'nome': 'Nome do produto',
            'categoria': 'Categoria',
            'fornecedor': 'Fornecedor',
            'quantidade_estoque': 'Quantidade em estoque',
            'estoque_minimo': 'Estoque mínimo',
            'preco_compra': 'Preço de compra (R$)',
            'preco_venda': 'Preço de venda (R$)',
            'data_cadastro': 'Data de cadastro',
            'data_ultima_entrada': 'Data da última entrada',
            'quantidade_entrada': 'Quantidade da última entrada',
            'unidade_medida': 'Unidade de medida',
            'localizacao_estoque': 'Localização no estoque',
            'ativo': 'Produto ativo',
        }
        widgets = {
            'data_cadastro': DateInput(),
            'data_ultima_entrada': DateInput(),
            'preco_compra': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'preco_venda': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _traduzir_opcao_vazia(self, {
            'categoria': 'Selecione uma categoria',
            'fornecedor': 'Selecione um fornecedor',
            'unidade_medida': 'Selecione a unidade',
        })

    def clean(self):
        dados = super().clean()
        compra = dados.get('preco_compra')
        venda = dados.get('preco_venda')
        if compra is not None and venda is not None and venda < compra:
            self.add_error('preco_venda', 'O preço de venda não pode ser menor que o preço de compra.')
        return dados


class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda
        fields = [
            'produto', 'data_venda', 'quantidade_vendida', 'preco_unitario',
            'desconto', 'forma_pagamento', 'vendedor', 'cliente', 'nota_cliente',
        ]
        labels = {
            'produto': 'Produto',
            'data_venda': 'Data da venda',
            'quantidade_vendida': 'Quantidade vendida',
            'preco_unitario': 'Preço unitário (R$)',
            'desconto': 'Desconto (R$)',
            'forma_pagamento': 'Forma de pagamento',
            'vendedor': 'Vendedor',
            'cliente': 'Cliente',
            'nota_cliente': 'Nota do cliente (1 a 5)',
        }
        widgets = {
            'data_venda': DateInput(),
            'preco_unitario': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'desconto': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'nota_cliente': forms.NumberInput(attrs={'min': '1', 'max': '5', 'step': '0.1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Só faz sentido vender produtos ativos.
        self.fields['produto'].queryset = Produto.objects.filter(ativo=True)
        _traduzir_opcao_vazia(self, {
            'produto': 'Selecione um produto',
            'forma_pagamento': 'Selecione a forma de pagamento',
        })

    def clean_quantidade_vendida(self):
        quantidade = self.cleaned_data['quantidade_vendida']
        if quantidade <= 0:
            raise forms.ValidationError('A quantidade vendida deve ser maior que zero.')
        return quantidade

    def clean(self):
        dados = super().clean()
        produto = dados.get('produto')
        quantidade = dados.get('quantidade_vendida')
        desconto = dados.get('desconto')
        preco = dados.get('preco_unitario')

        if produto and quantidade and quantidade > produto.quantidade_estoque:
            self.add_error(
                'quantidade_vendida',
                f'Quantidade vendida maior que o estoque disponível '
                f'({produto.quantidade_estoque} em estoque).',
            )

        if preco is not None and quantidade and desconto is not None:
            if desconto > preco * quantidade:
                self.add_error('desconto', 'O desconto não pode ser maior que o valor da venda.')

        return dados

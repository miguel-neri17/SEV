SEV — Sistema Inteligente de Controle de Estoque e Análise de Vendas

Aplicação web em Django para pequenos comércios: cadastro de produtos, registro de vendas com baixa automática de estoque e um painel que transforma esses lançamentos em indicadores.

Mercadinho de bairro costuma controlar estoque no caderno ou na memória. O resultado é sempre o mesmo: falta o que vende e sobra o que não gira. O SEV registra as vendas, mantém o estoque em dia sozinho e mostra onde o dinheiro realmente entra.

Projeto Integrador desenvolvido em grupo.

Funcionalidades

Cadastros

Produtos, com categoria, fornecedor, unidade de medida (unidade, caixa, pacote, kg, litro), preço de compra, preço de venda, localização no estoque e estoque mínimo
Categorias e fornecedores, com edição e exclusão
Busca de produtos por nome
Produtos podem ser desativados em vez de excluídos, preservando o histórico de vendas

Vendas

Registro com quantidade, preço unitário, desconto, forma de pagamento (Dinheiro, Pix, Cartão de Débito, Cartão de Crédito), vendedor, cliente e nota do cliente
O estoque é baixado automaticamente ao registrar a venda
Excluir uma venda devolve as unidades ao estoque

Dashboard

Totais de produtos, unidades em estoque, vendas, faturamento e lucro
Lista de produtos abaixo do estoque mínimo
Os cinco produtos mais vendidos
Quatro gráficos: estoque × vendas por categoria, faturamento por produto, faturamento por categoria e distribuição das formas de pagamento

Relatórios

Vendas por produto e por forma de pagamento
Produtos com estoque baixo
Faturamento e lucro consolidados

Acesso

Login obrigatório: nenhuma tela abre sem usuário autenticado
Cadastro de novos usuários pela própria aplicação
Decisões técnicas

Três pontos que valem ser olhados no código:

Baixa de estoque à prova de corrida. A venda e a baixa acontecem dentro de uma transaction.atomic, e a subtração usa F('quantidade_estoque') - quantidade em vez de ler e gravar em Python. Se duas vendas forem salvas ao mesmo tempo, nenhuma baixa se perde.

Exclusão que não apaga histórico. Categorias, fornecedores e produtos usam on_delete=PROTECT. Tentar excluir um produto que já vendeu não quebra o sistema: ele devolve uma mensagem explicando e sugere desativar o produto.

Gráficos sem biblioteca externa. Os quatro gráficos são desenhados em <canvas> puro, com animação de entrada própria, escala automática e respeito à preferência prefers-reduced-motion do sistema operacional. Nenhum Chart.js, nenhum CDN — a página funciona offline.

Os totais de faturamento e lucro são calculados pelo banco, em uma única consulta agregada, em vez de somados em laço no Python.

Tecnologias
	
Linguagem	Python
Framework	Django
Banco de dados	SQLite
Front-end	HTML, CSS e JavaScript (canvas)
Editor	VS Code
Como executar
bash
# 1. Clonar o repositório
git clone https://github.com/miguel-neri17/SEV.git
cd SEV

# 2. Criar e ativar o ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

# 3. Instalar o Django
pip install django

# 4. Criar as tabelas e o usuário padrão
python manage.py migrate

# 5. Subir o servidor
python manage.py runserver

Abra http://127.0.0.1:8000/ no navegador.

Acesso
Usuário	Senha
admin	admin123

O usuário é criado automaticamente pela migração 0002_usuario_padrao. Para recriar ou redefinir a senha:

bash
python manage.py configurar_projeto

É uma conta local de desenvolvimento. Em uso real, troque a senha.

Estrutura 

manage.py                    utilitário de linha de comando do Django
sev_project/                 configuração do projeto
  settings.py                idioma pt-br, fuso America/Sao_Paulo, SQLite
  urls.py
estoque/                     aplicação principal
  models.py                  Categoria, Fornecedor, Produto, Venda
  views.py                   dashboard, cadastros, vendas e relatórios
  forms.py
  urls.py
  migrations/                inclui a criação do usuário padrão
  management/commands/       comando configurar_projeto
  templates/estoque/         telas do sistema
  static/estoque/            style.css e graficos.js
db.sqlite3                   banco (criado pelo migrate, fora do versionamento)

A análise que originou o sistema

Antes do código, o grupo analisou uma base de vendas para entender o que um comércio pequeno precisa enxergar. Duas conclusões viraram decisão de projeto:

A média engana, a mediana não. Uma única venda muito grande puxou a média de quantidade vendida para quase o dobro da mediana. Repor estoque pela média significaria comprar demais quase sempre. A mediana é a referência mais honesta de giro.

Venda fora do padrão pede aviso, não correção. Aquela venda atípica não era erro — era um pedido grande de verdade. Em vez de descartá-la, o caminho é sinalizar vendas fora do padrão para o dono decidir se aquilo se repete.

O gráfico de faturamento por categoria é o que responde a pergunta que importa na hora de comprar: onde o dinheiro realmente entra.

<sub>Projeto acadêmico, desenvolvido em grupo.</sub>

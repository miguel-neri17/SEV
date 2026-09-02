# SEV — Sistema Inteligente de Controle de Estoque e Análise de Vendas

Aplicação web em Django + SQLite para controle de estoque, registro de vendas
e análise de indicadores para pequenos comércios.

## Como executar

```
cd SEV
venv\Scripts\activate        # Windows
python manage.py migrate     # cria as tabelas e o usuário padrão
python manage.py runserver
```

Abra http://127.0.0.1:8000/ no navegador.

## Acesso

O sistema exige login. Nenhuma tela (dashboard, produtos, vendas, categorias,
fornecedores ou relatórios) abre sem usuário autenticado.

| Usuário | Senha    |
|---------|----------|
| admin   | admin123 |

O usuário é criado automaticamente pela migração `0002_usuario_padrao`.
Para recriar ou redefinir a senha depois, rode:

```
python manage.py configurar_projeto
```

O botão **Sair**, no canto direito do cabeçalho, encerra a sessão e devolve
o usuário para a tela de login. A área `/admin/` do Django continua existindo
separadamente, para manutenção dos dados.

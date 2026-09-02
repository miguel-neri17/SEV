from django.db import migrations


def criar_usuario_padrao(apps, schema_editor):
    """Cria o login admin / admin123 usado para acessar o SEV.

    Roda junto com `python manage.py migrate`, então o sistema já nasce
    com um usuário pronto. Se o usuário já existir, nada é alterado.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    if User.objects.filter(username='admin').exists():
        return
    User.objects.create_superuser(
        username='admin',
        email='admin@sev.com',
        password='admin123',
    )


def remover_usuario_padrao(apps, schema_editor):
    from django.contrib.auth import get_user_model

    get_user_model().objects.filter(username='admin').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(criar_usuario_padrao, remover_usuario_padrao),
    ]

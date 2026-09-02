from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Cria o administrador padrão do projeto SEV.'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'admin'
        email = 'admin@sev.com'
        password = 'admin123'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        )
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()
        status = 'criado' if created else 'atualizado'
        self.stdout.write(self.style.SUCCESS(
            f'Administrador {status}: usuário={username} senha={password}'
        ))

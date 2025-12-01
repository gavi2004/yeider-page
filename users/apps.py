from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'  
    
    def ready(self):
        import users.signals  

    class Meta:
        verbose_name = "Usuarios"
        verbose_name_plural = "Usuarios"
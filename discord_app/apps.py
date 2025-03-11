from django.apps import AppConfig
from discord_app.bot import *


class DiscordConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'discord'
    
    
    def ready(self):
        start_bot_in_thread()  
  

    
    
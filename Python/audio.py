import vlc
import time

# Reproduce una pista de música para amenizar la espera durante la ejecución
def musica_ascensor():
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new('../Database/musica.mp3')
    player.set_media(media)
    player.play()

    timeout = time.time() + 120   # Dos minutos de música 
    while True:
        if time.time() > timeout:
            player.stop()


import vlc
import time

def musica_ascensor():
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new('../Database/musica.mp3')
    player.set_media(media)
    player.play()

    timeout = time.time() + 60   # Aquí tenemos que poner nosotros el timeout
    while True:
        if time.time() > timeout:
            player.stop()


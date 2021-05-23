
from pygame import mixer
import time
def musica_ascensor(a):
    mixer.init()
    mixer.music.load(r'Database/musica.mp3')
    mixer.music.set_volume(1.0)
    mixer.music.play(loops = -1)
    if (a == True):
        time.sleep(5)
    else: 
        mixer.music.stop()


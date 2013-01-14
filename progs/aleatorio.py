import curses
import time
import random

name = 'Aleatorio'

def program(cur_track, note_lists, perf, window):
    window.clear()
    curses.echo()
    window.addstr(6, 4, 'Numero de tonos: ')
    num = window.getstr()
    curses.noecho()
    if not num.isdigit():
        window.addstr(10, 4, 'Entrada invalida!')
        window.refresh()
        time.sleep(1)
        return
    new_list = ''
    tones = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    durs = ['B', 'N', 'C']
    for i in range(int(num)):
        new_tone = tones[random.randint(0, len(tones)-1)]
        new_dur = durs[random.randint(0, len(durs)-1)]
        octave = random.randint(1,6)
        new_list += '%i%s %s\n'%(octave,new_tone, new_dur)
    note_lists[cur_track] = new_list
    window.addstr(10, 8, 'Aleatorio generado')
    window.refresh()
    time.sleep(1)
        

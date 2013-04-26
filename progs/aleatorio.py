import curses
import time
import random

name = 'Aleatorio'

def program(cur_track, note_lists, perf, window):
    window.clear()
    curses.echo()
    window.addstr(6, 4, 'Numero de tonos: ')
    num = window.getstr()
    window.addstr(7, 4, 'Altura minima (0-127): ')
    min_pitch = window.getstr()
    window.addstr(8, 4, 'Altura maxima (0-127): ')
    max_pitch = window.getstr()
    curses.noecho()
    
    if not num.isdigit() or not max_pitch.isdigit() or not min_pitch.isdigit():
        window.addstr(10, 4, 'Entrada invalida!')
        window.refresh()
        time.sleep(1)
        return

    new_list = ''
    tones = ['C', 'CS', 'D', 'DS', 'E', 'F', 'FS', 'G', 'GS', 'A', 'AS', 'B']
    durs = ['B', 'N', 'C']
    for i in range(int(num)):
        new_pitch = random.randint(int(min_pitch), int(max_pitch))
        new_tone = tones[new_pitch%12]
        new_dur = durs[random.randint(0, len(durs)-1)]
        octave = int(new_pitch/12)
        new_list += '%i%s %s\n'%(octave,new_tone, new_dur)
    note_lists[cur_track] = new_list
    window.addstr(10, 8, 'Aleatorio generado')
    window.refresh()
    time.sleep(1)
        

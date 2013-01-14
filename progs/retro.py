import curses
import time

name = 'Retrogrado'

def program(cur_track, note_lists, perf, window):
    l = note_lists[cur_track]
    new_l =[note for note in reversed(l)]
    # TODO need to move octave and other carry properties
    note_lists[cur_track] = new_l
    window.clear()
    window.addstr(10, 8, 'Retrogrado')
    window.refresh()
    time.sleep(2)
        


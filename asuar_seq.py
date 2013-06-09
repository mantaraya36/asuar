# -*- coding: utf-8 -*-

import csnd
import time
import pyduino
from threading import Thread
import curses
from curses.textpad import Textbox
import os
import pickle
import sys

kblocks = 0

cs = None
perf = None
arduino = None
stdscr = None
outerscr = None
t = None
num_tracks = 6
cur_track = 0
tempo = 60

VERSION = '0.1' 
SEQS_DIR = 'seqs'
PROG_DIR = 'progs'

def init_data():
    global parameters, parameter_names, note_lists
    parameters = {"outlevel": 0.9,
              "out": 0.9,
              "att": 0.01,
              "dec": 0.01,
              "sus": 0.5,
              "rel": 0.5,
              "fatt": 0.1,
              "fdec": 0.1,
              "fsus": 0.5,
              "frel": 0.5,
              "fenvamount": 0.5,
              "cf": 1000,
              "res": 0.9,
              "pan": 0.5,
              "rm1": 0.1,
              "rm2": 0.1,

              "revmix": 0.6,
              "Roomsize": 0.8,
              "HFDamp": 0.8,
    
              # "lfo1shape": 1,
              # "lfo1amt": 1,
              # "lfo1freq": 1,
              # "lfo1patch": 1,
              # "lfo1dest": 1,
              # "lfo2shape": 1,
              # "lfo2amt": 1,
              # "lfo2freq": 1,
              # "lfo2patch": 1,
              # "lfo2dest": 1,
              "rm1amount": 1,
              "rm1rate": 200,
              "rm1torm2": 1,
              "rm2amount": 1,
              "rm2rate": 45 }

    parameter_names = {"outlevel": "Nivel de salida (0-1)",
                   "out": "Salida (0-1)",
                   "att": "Ataque (s)",
                   "dec": "Decaida (s)",
                   "sus": "Nivel de mantenimiento (0-1)",
                   "rel": "Liberacion (s)",
                   "fatt": "Attaque filtro (s)",
                   "fdec": "Decaida filtro (s)",
                   "fsus": "Nivel mantenimiento filtro (0-1)",
                   "frel": "Liberacion filtro (s)",
                   "fenvamount": "Cantidad envolvente filtro (0-1)",
                   "cf": "Frequencia de corte (Hz)",
                   "res": "Resonancia (0-1)",
                   "pan": "Paneo (0-1)",
                   "rm1": "Modulacion anillo 1 (0-1)",
                   "rm2": "Modulacion anillo 2 (0-1)",

                   "revmix": "Reverberacion (0-1)",
                   "Roomsize": "Tamano reverberacion (0-1)",
                   "HFDamp": "Atenuacion altos rev. (0-1)",
                   
                   # "lfo1shape": "Forma LFO",
                   # "lfo1amt": "Cantidad LFO (0-1)",
                   # "lfo1freq": 1,
                   # "lfo1patch": 1,
                   # "lfo1dest": 1,
                   # "lfo2shape": 1,
                   # "lfo2amt": 1,
                   # "lfo2freq": 1,
                   # "lfo2patch": 1,
                   # "lfo2dest": 1,
                   "rm1amount": "Cantidad Mod. anillo 1 (0-1)",
                   "rm1rate": "Frequencia mod. anillo 1 (Hz)",
                   "rm1torm2": "Mod. 1 a Mod 2 (0-1)",
                   "rm2amount": "Cantidad Mod. anillo 2 (0-1)",
                   "rm2rate": "Frequencia mod. anillo 1 (Hz)" }
    note_lists = ['\n' for i in range(num_tracks)]

def read_arduino():
    global parameters, arduino
    while True:
        arduino.iterate()
        parameters['res'] = (arduino.analog[1].read()/2.0) + 0.48
        parameters['cf'] = (arduino.analog[0].read()*6000)+100
        #parameters['fenvamount'] = arduino.analog[2].read()
        parameters['rm1'] = arduino.analog[2].read()
        parameters['rm1rate'] = (arduino.analog[3].read()*50) + 10
        parameters['revmix'] = arduino.analog[4].read()

def init_arduino():
    global arduino
    arduino_devs = ['/dev/ttyUSB0', '/dev/ttyACM0']
    dev = ''
    for d in arduino_devs:
        if os.path.exists(d):
            dev = d
            break
    if not dev:
        return
    arduino = pyduino.Arduino(dev)
    arduino.analog[0].set_active(1)
    arduino.analog[1].set_active(1)
    arduino.analog[2].set_active(1)
    arduino.analog[3].set_active(1)
    arduino.analog[4].set_active(1)
    arduino.analog[5].set_active(1)
    arduino.iterate()
    while arduino.analog[0].read() == -1 or arduino.analog[1].read() == -1 \
            or arduino.analog[2].read() == -1 or arduino.analog[3].read() == -1 \
            or arduino.analog[4].read() == -1 or arduino.analog[5].read() == -1:
        arduino.iterate()
    t = Thread(target=read_arduino)
    t.start()
    

def cb(csound):
    global kblocks
    global parameters
    kblocks += 1
    params = ['cf', 'res', 'rm1','revmix', 'rm1rate']
    for p in params:
        csound.SetChannel(p, parameters[p])


def start_csound():
# create empty orchestra and score
    cs_ = csnd.Csound()
    cs_.SetMessageCallback(None)
    cs_.Compile("asuar.csd")
# create the thread object
    perf_ = csnd.CsoundPerformanceThread(cs_)
# set the callback
    perf_.SetProcessCallback(cb, cs_)
    return cs_, perf_

def show_initial_screen():
    stdscr.clear()
    y,x = stdscr.getmaxyx()
    title =  "* * * * C O M D A S U A R   II * * * * "
    stdscr.addstr(y/3, (x - len(title))/2, title)
    stdscr.addstr(0, x - 8, "v" + VERSION)
    title =  "COMPUTADOR MUSICAL"
    stdscr.addstr(y/3 + 3 , (x - len(title))/2, title)
    title =  "DIGITAL ASUAR"
    stdscr.addstr(y/3 + 5 , (x - len(title))/2, title)
    title =  "* * * * *  A S U A R * * * * *"
    stdscr.addstr(y/3 + 7 , (x - len(title))/2, title)
    stdscr.move(y-3,0)
    stdscr.refresh()

def show_help_window():
    y,x = stdscr.getmaxyx()
    stdscr.clear()
    stdscr.refresh()
    helpwin = stdscr.subwin(y-3, x-10, 2, 5)
    helpwin.border()
    helpwin.addstr(1, 5, "Por: Andres Burbano y Andres Cabrera", curses.A_BOLD)
    helpwin.addstr(3, 5, "Licencia:")
    helpwin.addstr(5, 5, "Implementacion del sintetizador COMDASUAR")
    helpwin.addstr(6, 5, "para Raspberry Pi.")
    helpwin.addstr(8, 5, "Pagina web")
    helpwin.refresh()
    for i in range(60):
        perf.InputMessage("i 2 %f 0.05 %i %i 1"%(i/10.0, 110+(i*44), 100 - i))
    helpwin.getch()
    helpwin.clear()
    helpwin.refresh()
    del helpwin

def write_main_menu():
    y,x = stdscr.getmaxyx()
    print_header(x,y)

    stdscr.addstr(3, 14, "Menu principal", curses.A_UNDERLINE | curses.A_BOLD)
    stdscr.addstr(5, 8, "1 - Nuevo")
    stdscr.addstr(6, 8, "2 - Cargar")
    stdscr.addstr(7, 8, "3 - Salvar")
    stdscr.addstr(8, 8, "4 - Secuenciador")
    stdscr.addstr(9, 8, "5 - Editor de parametros")
    stdscr.addstr(11, 8, "a- Ayuda")
    stdscr.addstr(13, 8, "0 - Salir")
    stdscr.refresh()


def main_menu():
    write_main_menu()
    while True:
        c = stdscr.getch()
        if c == ord('1'):
            new_file()
            write_main_menu()
        elif c == ord('2'):
            load_file()
            write_main_menu()
        elif c == ord('3'):
            save_file()
            write_main_menu()
        elif c == ord('4'):
            show_sequencer()
            write_main_menu()
        elif c == ord('5'):
            make_parameter_editor()
            write_main_menu()
        elif c == ord('a'):
            show_help_window()
            write_main_menu()
        elif c == ord('0'):
            break
        else:
            y,x = stdscr.getmaxyx()
            stdscr.addstr(y-3, 8, "Opcion invalida!")
            stdscr.refresh()
        
def new_file():
    init_data()
    stdscr.clear()
    stdscr.addstr(5, 4, "Datos inicializados.", curses.A_REVERSE)
    stdscr.refresh()
    time.sleep(2)
    write_main_menu()

def load_file():
    global note_lists, parameters
    files = os.listdir(SQS_DIR)
    stdscr.clear()
    stdscr.scrollok(True)
    if not files:
        stdscr.addstr(5, 4, "No existen archivos salvados", curses.A_REVERSE)
        stdscr.refresh()
        time.sleep(2)
        return
    stdscr.addstr(0, 5, "Seleccione el archivo. Presione 'q' para cancelar. ", curses.A_REVERSE)
    stdscr.move(1,0)
    for file in files:
        stdscr.addstr("    " + file + "\n")
    stdscr.move(1,0)
    stdscr.chgat(curses.A_REVERSE)
    while True:
        c = stdscr.getch()
        if c == curses.KEY_UP:
            y,x = stdscr.getyx()
            if y > 1:
                stdscr.chgat(curses.A_NORMAL)
                stdscr.move(y - 1, 0) 
                stdscr.chgat(curses.A_REVERSE)
        elif c == curses.KEY_DOWN:
            y,x = stdscr.getyx()
            if y < stdscr.getmaxyx()[0] - 1:
                stdscr.chgat(curses.A_NORMAL)
                stdscr.move(y + 1, 0)
                stdscr.chgat(curses.A_REVERSE)
        elif c == ord('q'):
            stdscr.clear()
            stdscr.addstr(5, 4, "Cancelado.", curses.A_REVERSE)
            stdscr.refresh()
            time.sleep(2)
            write_main_menu()
            return
        else:
            break
    y,x = stdscr.getmaxyx()
    name = stdscr.instr(x).strip()
    if not name:
        stdscr.clear()
        stdscr.addstr(5, 4, "Cancelado.", curses.A_REVERSE)
        stdscr.refresh()
        time.sleep(2)
        write_main_menu()
        return
    with open(SEQS_DIR + '/' + name, 'rb') as handle:
        out = pickle.loads(handle.read())
    
    parameters = out['parameters']
    note_lists = out['note_lists']
    stdscr.clear()
    stdscr.addstr(5, 4, "Archivo '%s' cargado"%name, curses.A_REVERSE)
#    stdscr.addstr(6, 4, str(note_lists), curses.A_REVERSE)
    stdscr.refresh()
    time.sleep(2)
    stdscr.scrollok(False)

def save_file():
    stdscr.clear()
    stdscr.addstr(3, 2, "Nombre del archivo: ")
    curses.echo()
    curses.curs_set(1)
    name = stdscr.getstr().strip()
    curses.noecho()
    curses.curs_set(0)
    if os.path.exists(SEQS_DIR + '/' + name):
        stdscr.addstr(5, 4, "Error, archivo ya existe!", curses.A_REVERSE)
        stdscr.addstr(6, 4, "Sobreescribir (S/N)?")
        stdscr.refresh()
        if stdscr.getch() != ord('s'):
            stdscr.addstr(7, 4, "Cancelado", curses.A_REVERSE)
            time.sleep(2)
            write_main_menu()
            return

    with open(SEQS_DIR + '/' + name, 'wb') as handle:
        out = {'version': 1,
               'note_lists': note_lists,
               'parameters': parameters}
        pickle.dump(out, handle)

    stdscr.addstr(7, 4, "Archivo '%s' salvado"%name, curses.A_REVERSE)
    stdscr.refresh()
    time.sleep(2)

    write_main_menu()

def write_sequencer():
    y,x = stdscr.getmaxyx()
    print_header(x,y)

    stdscr.addstr(3, 14, "Secuenciador - Pista %i"%cur_track,
                  curses.A_UNDERLINE | curses.A_BOLD)
    stdscr.addstr(5, 8, "1 - Editar")
    stdscr.addstr(6, 8, "2 - Reproducir pista")
    stdscr.addstr(7, 8, "3 - Reproducir todo")
    stdscr.addstr(8, 8, "4 - Programa")
    stdscr.addstr(9, 8, "5 - Cambiar pista")
    stdscr.addstr(10, 8, "6 - Cambiar Tempo (Actual: %f)"%tempo)

    stdscr.addstr(15, 8, "0 - Regresar")
    stdscr.refresh()    

def show_sequencer():
    while True:
        write_sequencer()
        c = stdscr.getch()
        if c == ord('1'):
            make_text_editor()
        elif c == ord('2'):
            play_sequence(cur_track)
        elif c == ord('3'):
            play_sequence()
        elif c == ord('4'):
            run_program()
        elif c == ord('5'):
            change_track()
        elif c == ord('6'):
            change_tempo()
        elif c == ord('0'):
            break

def convert_to_csound(asuar_text):
    lines = asuar_text.upper().splitlines()
    csound_text = ''
    cur_octave = 4
    cur_pitch = 0
    cur_alt = 0
    cur_plet = 0
    cur_dur = 1
    pos = 0
    durations = {'R': 4, 'B':2, 'C':0.5, 'N':1, 'S':0.25, 'F':0.125, 'M':0625}
    pitches = {'C':0, 'D':2, 'E':4, 'F':5, 'G':7, 'A':9, 'B':11}
# FIXME fix alteration values from docs
    alterations = {'S':1, 'W':-1, 'Q':0, 'U':0, 'T': 0, 'V':0, 'R': 0}
    for line in lines:
        if not line:
            continue
        note,dur, = line.split()
        if dur[0].isdigit():
            cur_plet = int(dur[0])
            dur = dur[1:]
        
        if dur:
            cur_dur = 0
            for d in dur:
                cur_dur += durations[d]

        cur_dur = cur_dur * 60/tempo
        if note[0] == 'R':
            pos += cur_dur
            continue
        if note[0].isdigit():
            cur_octave = int(note[0])
            note = note[1:]
        if note:
            cur_pitch = pitches[note[0]]
            if len(note) > 1:
                cur_alt = alterations[note[1]]
        midi_pitch = (12 * (cur_octave + 1)) + cur_pitch + cur_alt
        pitch = 440 * (2**((midi_pitch-69)/12.0))
        new_note = 'i 2 %f %f %f %f\n'%(pos, cur_dur, pitch, 100)
        csound_text += new_note
        pos += cur_dur
    return csound_text

def play_sequence(track = -1):
    if track >= 0:
        try:
            perf.InputMessage(convert_to_csound(note_lists[cur_track]))
        except:
            stdscr.clear()
            stdscr.addstr(5, 4, "Error compilando pista.", curses.A_REVERSE)
            stdscr.refresh()
            time.sleep(2)
            write_main_menu()
    else:
        for i in range(num_tracks):
            try:
                perf.InputMessage(convert_to_csound(note_lists[i]))
            except:
                stdscr.clear()
                stdscr.addstr(5, 4, "Error compilando pista %i."%(i+1), curses.A_REVERSE)
                stdscr.refresh()
                time.sleep(2)
                write_main_menu()

def print_header(x,y):
    stdscr.clear()
    stdscr.addstr(0, (x/2)- 12, "**** COMDASUAR mk II ****")
    stdscr.addstr(0, x- 5, "v" + VERSION)
    
def write_program_list(progs):
    y,x = stdscr.getmaxyx()
    print_header(x,y)

    stdscr.addstr(3, 14, "Programas Heuristicos", curses.A_UNDERLINE | curses.A_BOLD)
    for i,prog in enumerate(progs):
        stdscr.addstr(i + 4, 8, "%i - %s"%(i+ 1, prog))

    stdscr.addstr(15, 8, "0 - Regresar")
    stdscr.refresh()    

def run_prog(prog):
    try:
        line = "from %s import program"%(prog[:-3])
        exec(line)
        program(cur_track, note_lists, perf, stdscr)
    except Exception as e:
        stdscr.clear()
        stdscr.addstr(10, 3, "Error:" + str(e))
        stdscr.refresh()
        time.sleep(2)
        
def run_program():
    progs = os.listdir(PROG_DIR)
    for p in progs:
        if not p.endswith('.py'):
            progs.remove(p)
    while True:
        write_program_list(progs)
        c = stdscr.getkey()
        if c == '0':
            break
        if not c.isdigit():
            pass
        index = int(c) - 1
        if index < len(progs):
            run_prog(progs[index])

def change_track():
    global cur_track
    y,x = stdscr.getmaxyx()
    print_header(x,y)
    curses.echo()
    stdscr.addstr(6, 4, 'Cambiar a pista: ')
    num = stdscr.getstr()
    curses.noecho()
    tr = int(num)
    if not num.isdigit() or tr < 0 or tr > num_tracks:
        stdscr.addstr(10, 4, 'Entrada invalida!')
        stdscr.refresh()
        time.sleep(1)
        return
    cur_track = tr
    
def change_tempo():
    global tempo
    y,x = stdscr.getmaxyx()
    print_header(x,y)
    curses.echo()
    stdscr.addstr(6, 4, 'Cambiar a tempo (Actual: %f): '%tempo)
    num = stdscr.getstr()
    curses.noecho()
    new_tempo = float(num)
    if new_tempo < 20 or new_tempo > 300:
        stdscr.addstr(10, 4, 'Entrada invalida!')
        stdscr.refresh()
        time.sleep(1)
        return
    tempo = new_tempo

# This scrolling screen by Lyle Scott III
# lyle@digitalfoo.net
    
topLineNum = 0
highlightLineNum = 0

SPACE_KEY = 32
ESC_KEY = 27

def displayScreen(screen):
    global topLineNum, highlightLineNum
    screen.clear()

    # now paint the rows
    bottom = topLineNum + curses.LINES -3
    lines = note_lists[cur_track].split('\n')
    screen.bkgd(' ', curses.A_REVERSE)
    for (index,line,) in enumerate(lines[topLineNum:bottom]):
        linenum = topLineNum + index
        line = '%04i %s' % (linenum, line,)

        # highlight current line            
        if index != highlightLineNum:
            screen.addstr(index, 0, line, curses.A_REVERSE)
        else:
            screen.addstr(index, 0, line, curses.A_BOLD | curses.A_REVERSE)

    screen.move(highlightLineNum, 5)
    screen.refresh()


def updown(increment, nOutputLines):
    global topLineNum, highlightLineNum
    nextLineNum = highlightLineNum + increment

    # paging
    if increment == -1 and highlightLineNum == 0 and topLineNum != 0:
        topLineNum += -1 
        return
    elif increment == 1 and nextLineNum == curses.LINES - 3 and (topLineNum+curses.LINES - 3) != nOutputLines:
        topLineNum += 1
        return

    # scroll highlight line
    if increment == -1 and (topLineNum != 0 or highlightLineNum != 0):
        highlightLineNum = nextLineNum
    elif increment == 1 and (topLineNum+highlightLineNum+1) != nOutputLines and highlightLineNum != curses.LINES- 3:
        highlightLineNum = nextLineNum

def addLine():
    global topLineNum, highlightLineNum
    lines = note_lists[cur_track].split('\n')
    lines.insert(highlightLineNum + 1, '')
    note_lists[cur_track] = '\n'.join(lines)
    highlightLineNum += 1

def deleteLine():
    global topLineNum, highlightLineNum
    lines = note_lists[cur_track].split('\n')
    if len(lines) > 2: 
        lines.pop(highlightLineNum)
    if highlightLineNum >= len(lines):
        highlightLineNum -= 1
    note_lists[cur_track] = '\n'.join(lines)

def editLine(editwin):
    lines = note_lists[cur_track].split('\n')
    linewin = editwin.subwin(1, curses.COLS - 5, highlightLineNum + 1, 5)
    linewin.addstr(0, 0, lines[highlightLineNum])
    linewin.bkgd(' ')
    editpad = Textbox(linewin)
    new_line = editpad.edit()
    lines[highlightLineNum] = new_line
    note_lists[cur_track] = '\n'.join(lines)
    
def make_text_editor():
    global topLineNum, highlightLineNum
    y,x = stdscr.getmaxyx()
    stdscr.addstr(y-2, 3, "Presione Ctrl+G para salir")
    #    curses.curs_set(1)
#    editwin = outerscr.subwin(curses.LINES - 2, curses.COLS- 5, 1, 4)
    editwin = stdscr.subwin(curses.LINES - 3, curses.COLS, 1, 0)
    editwin.clear()
    editwin.scrollok(True)
    topLineNum = 0
    highlightLineNum = 0
    while True:
        displayScreen(editwin)
        # get user command
        c = editwin.getch()
        nOutputLines = len(note_lists[cur_track].split('\n'))
        if c == curses.KEY_UP or c == ord('w'): 
            updown(-1, nOutputLines)
        elif c == curses.KEY_DOWN or c == ord('x'):
            updown(1, nOutputLines)
        elif c == curses.KEY_ENTER or c == ord('d'):
            addLine()
        elif  c == ord('j'):
            deleteLine()
        elif c == SPACE_KEY:
            editLine(editwin)
        elif c == ESC_KEY  or c == ord('q'):
            break
    # editpad = Textbox(editwin)
    # note_lists[cur_track] = editpad.edit()
    # editwin.bkgd(' ', curses.A_NORMAL)
    # editwin.clear()
    #  curses.curs_set(0)
    del editwin
    #del editpad

def make_parameter_editor():
    y,x = stdscr.getmaxyx()
    print_header(x,y)
    stdscr.addstr(3, 14, "Parametros", curses.A_UNDERLINE | curses.A_BOLD)

    row = 5
    for key in parameters.keys():
        stdscr.addstr(row, 8, parameter_names[key] + ':' + str(parameters[key]))
        row = row + 1
        if row > y - 4:
            break
    stdscr.refresh()
    while True:
       c = stdscr.getch()
       if c == ord('0'): break  # Exit the while()
       elif c == ord('m'): break


def key_pressed(text):
    freq = -220 + (ord(text[0])*10)
    perf.InputMessage("i 2 0 1 %f 100 1"%freq)

def main():
    global cs, perf, outerscr, stdscr
    init_data()
    sys.path.insert(0,PROG_DIR)

    stdscr = curses.initscr()
    stdscr.keypad(1)
    #outerscr = curses.initscr()
    #outerscr.keypad(1)

    curses.noecho()
    curses.cbreak()
    #   curses.curs_set(0)

    #y,x = outerscr.getmaxyx()
    #stdscr = outerscr.subwin(y-3, x-6, 1, 3)

    show_initial_screen()

    init_arduino()
    if arduino is not None:
        stdscr.addstr("Arduino inicializado.\n")
    else:
        stdscr.addstr("Arduino no detectado\n")
    stdscr.refresh()

    stdscr.addstr("Iniciando Csound...")
    stdscr.refresh()
    cs,perf = start_csound()

    for key in parameters.keys():
        cs.SetChannel(key, parameters[key])

    perf.Play()
    stdscr.addstr("corriendo.\n")
    stdscr.refresh()

    perf.InputMessage("i 2 0 0.3 440 100 1")
    perf.InputMessage("i 2 0.5 0.5 880 100 1")
    perf.InputMessage("i 2 1 0.5 220 100 1")
    perf.InputMessage("i 2 1.5 0.5 660 100 1")
    perf.InputMessage("i 2 2 2 110 100 1")

    time.sleep(4)
    stdscr.clear()

    main_menu()


def cleanup():
    global outerscr
    perf.Stop()
    curses.nocbreak()
    #outerscr.keypad(0)
    stdscr.keypad(0)
    curses.echo()

    # curses.curs_set(1)
    curses.endwin()
    if t is not None:
        t.stop()
    print "Finalizado.\n"


if __name__ == "__main__":
    #time.sleep(1000)
    if not os.path.exists(SEQS_DIR):
        os.makedirs(SEQS_DIR)
    main()
    cleanup()

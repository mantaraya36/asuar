# -*- coding: utf-8 -*-

import csnd
import time
import pyduino
from threading import Thread
import curses
from curses.textpad import Textbox
import os
import pickle

cf = 1000
res = 0.9

kblocks = 0

cs = None
perf = None
arduino = None
stdsrc = None
t = None
num_tracks = 6
cur_track = 0

VERSION = '0.1' 
SEQS_DIR = 'seqs'

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
              "rm1rate": 1,
              "rm1torm2": 1,
              "rm2amount": 1,
              "rm2rate": 1 }

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
    note_lists = ['' for i in range(num_tracks)]

def read_arduino():
    global cf, res, arduino
    while True:
        arduino.iterate()
        cf = (arduino.analog[1].read()*6000)+100
        res = (arduino.analog[0].read()/2.0) + 0.48
        #print res

def init_arduino():
    global arduino
    try:
        arduino = pyduino.Arduino('/dev/ttyUSB0')
        arduino.analog[0].set_active(1)
        arduino.analog[1].set_active(1)
        arduino.analog[2].set_active(1)
        arduino.analog[3].set_active(1)
        arduino.analog[4].set_active(1)
        arduino.analog[5].set_active(1)
        arduino.iterate()
        while arduino.analog[0].read() == -1 or arduino.analog[1].read() == -1 :
            arduino.iterate()
        t = Thread(target=read_arduino)
        t.start()
    except:
        arduino = None


def cb(csound):
    global kblocks
    global cf, res
    kblocks += 1
    csound.SetChannel("cf", cf)
    csound.SetChannel("res", res)

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
    stdscr.addstr(y/3, (x/2)- 10, "**** COMDASUAR mk II ****")
    stdscr.addstr(0, x - 8, "v" + VERSION)
    stdscr.move(y-3,0)
    stdscr.refresh()

def show_help_window():
    y,x = stdscr.getmaxyx()
    helpwin = curses.newwin(y-4, x-10, 2, 5)
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
    del helpwin

def write_main_menu():
    y,x = stdscr.getmaxyx()
    stdscr.clear()
    stdscr.addstr(0, (x/2)- 12, "**** COMDASUAR mk II ****")
    stdscr.addstr(0, x- 5, "v" + VERSION)

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
    files = os.listdir(SEQS_DIR)
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
    stdscr.clear()
    stdscr.addstr(0, (x/2)- 12, "**** COMDASUAR mk II ****")
    stdscr.addstr(0, x- 5, "v" + VERSION)

    stdscr.addstr(3, 14, "Secuenciador", curses.A_UNDERLINE | curses.A_BOLD)
    stdscr.addstr(5, 8, "1 - Editar")
    stdscr.addstr(6, 8, "2 - Reproducir")
    stdscr.addstr(7, 8, "3 - Programa")

    stdscr.addstr(15, 8, "0 - Regresar")
    stdscr.refresh()    

def show_sequencer():
    while True:
        write_sequencer()
        c = stdscr.getch()
        if c == ord('1'):
            make_text_editor()
        elif c == ord('2'):
            pass
        elif c == ord('3'):
            run_program()
        elif c == ord('0'):
            break

def write_program_list():
    y,x = stdscr.getmaxyx()
    stdscr.clear()
    stdscr.addstr(0, (x/2)- 12, "**** COMDASUAR mk II ****")
    stdscr.addstr(0, x- 5, "v" + VERSION)

    stdscr.addstr(3, 14, "Programas Heuristicos", curses.A_UNDERLINE | curses.A_BOLD)
    stdscr.addstr(5, 8, "1 - ")
    stdscr.addstr(6, 8, "2 - ")
    stdscr.addstr(7, 8, "3 - ")

    stdscr.addstr(15, 8, "0 - Regresar")
    stdscr.refresh()    

def run_program():
    while True:
        write_program_list()
        c = stdscr.getch()
        if c == ord('1'):
            pass
        elif c == ord('2'):
            pass
        elif c == ord('3'):
            pass
        elif c == ord('4'):
            pass
        elif c == ord('5'):
            pass
        elif c == ord('0'):
            break

def make_text_editor():
    y,x = stdscr.getmaxyx()
    stdscr.addstr(y-1, 3, "Presione Ctrl+G para salir")
    for i in range(y-2):
        stdscr.addstr(i+1, 0, "%d"%i)
    stdscr.refresh()
    curses.curs_set(1)
    editwin = stdscr.subwin(curses.LINES - 2, curses.COLS- 5, 1, 4)
    editwin.clear()
    editwin.addstr(note_lists[cur_track])
    editwin.bkgd(' ', curses.A_REVERSE)
    editpad = Textbox(editwin)
    note_lists[cur_track] = editpad.edit()
    editwin.bkgd(' ', curses.A_NORMAL)
    editwin.clear()
    curses.curs_set(0)
    del editwin
    del editpad

def make_parameter_editor():
    y,x = stdscr.getmaxyx()
    stdscr.clear()
    stdscr.addstr(0, (x/2)- 12, "**** COMDASUAR mk II ****")
    stdscr.addstr(0, x- 5, "v" + VERSION)
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
       if c == ord('q'): break  # Exit the while()
       elif c == ord('m'): break


def key_pressed(text):
    freq = -220 + (ord(text[0])*10)
    perf.InputMessage("i 2 0 1 %f 100 1"%freq)

def main():
    global cs, perf, stdscr
    init_data()
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)
    curses.curs_set(0)

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

#    time.sleep(4)
    stdscr.clear()

    main_menu()


def cleanup():
    global stdscr
    perf.Stop()
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()

    curses.curs_set(1)
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

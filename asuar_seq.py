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

# globals
cs = None
perf = None
arduino = None
t = None
num_tracks = 6
cur_track = 0
tempo = 60
display = None
parameters = None
note_lists = None

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
    params = ['cf', 'res', 'rm1', 'revmix', 'rm1rate']
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

# FIXME better separation of GUI and data
class Screen:
    def __init__(self):
        self.stdscr = None
        self.stdscr = curses.initscr()
        #self.stdscr.keypad(1)
    
        curses.noecho()
        curses.cbreak()
        #   curses.curs_set(0)

    def cleanup(self):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

    def print_header(self, x,y):
        self.stdscr.clear()
        self.stdscr.addstr(0, (x/2)- 12, "**** COMDASUAR mk II ****")
        self.stdscr.addstr(0, x- 5, "v" + VERSION)

    def show_fs_message(self, message, delay=2, style=curses.A_REVERSE):
        self.stdscr.clear()
        self.stdscr.addstr(5, 4, message, style)
        self.stdscr.refresh()
        time.sleep(delay)
        
    def append_text(self, text):
        self.stdscr.addstr(text);
        self.stdscr.refresh()       

    def show_initial_screen(self):
        self.stdscr.clear()
        y,x = self.stdscr.getmaxyx()
        title =  "* * * * C O M D A S U A R   II * * * * "
        self.stdscr.addstr(y/3, (x - len(title))/2, title)
        self.stdscr.addstr(0, x - 8, "v" + VERSION)
        title =  "COMPUTADOR MUSICAL"
        self.stdscr.addstr(y/3 + 3 , (x - len(title))/2, title)
        title =  "DIGITAL ASUAR"
        self.stdscr.addstr(y/3 + 5 , (x - len(title))/2, title)
        title =  "* * * * *  A S U A R * * * * *"
        self.stdscr.addstr(y/3 + 7 , (x - len(title))/2, title)
        self.stdscr.move(y-3,0)
        self.stdscr.refresh()

    def show_help_window(self):
        y,x = self.stdscr.getmaxyx()
        self.stdscr.clear()
        self.stdscr.refresh()
        helpwin = self.stdscr.subwin(y-3, x-10, 2, 5)
        helpwin.border()
        helpwin.addstr(1, 5, "Por: Andres Burbano y Andres Cabrera", curses.A_BOLD)
        helpwin.addstr(3, 5, "Licencia: GPL")
        helpwin.addstr(5, 5, "Implementacion del sintetizador COMDASUAR")
        helpwin.addstr(6, 5, "para Raspberry Pi.")
        helpwin.addstr(8, 5, "https://github.com/mantaraya36/asuar")
        helpwin.refresh()
        for i in range(60):
            perf.InputMessage("i 2 %f 0.05 %i %i 1"%(i/10.0, 110+(i*44), 100 - i))
        helpwin.getch()
        helpwin.clear()
        helpwin.refresh()
        del helpwin

    def write_main_menu(self):
        y,x = self.stdscr.getmaxyx()
        self.print_header(x,y)
        self.stdscr.addstr(3, 14, "Menu principal", curses.A_UNDERLINE | curses.A_BOLD)
        self.stdscr.addstr(5, 8, "1 - Nuevo")
        self.stdscr.addstr(6, 8, "2 - Cargar")
        self.stdscr.addstr(7, 8, "3 - Salvar")
        self.stdscr.addstr(8, 8, "4 - Secuenciador")
        self.stdscr.addstr(9, 8, "5 - Editor de parametros")
        self.stdscr.addstr(11, 8, "a- Ayuda")
        self.stdscr.addstr(13, 8, "0 - Salir")
        self.stdscr.refresh()


    def main_menu(self):
        self.write_main_menu()
        while True:
            c = self.stdscr.getch()
            if c == ord('1'):
                self.new_file()
                self.write_main_menu()
            elif c == ord('2'):
                self.load_file()
                self.write_main_menu()
            elif c == ord('3'):
                self.save_file()
                self.write_main_menu()
            elif c == ord('4'):
                self.run_sequencer()
                self.write_main_menu()
            elif c == ord('5'):
                self.make_parameter_editor()
                self.write_main_menu()
            elif c == ord('a'):
                self.show_help_window()
                self.write_main_menu()
            elif c == ord('0'):
                break
            else:
                self.show_fs_message("Opcion invalida")
                self.write_main_menu()
        
    def new_file(self):
        init_data()
        display.show_fs_message("Datos inicializados.")
        self.write_main_menu()

    def load_file(self):
        global note_lists, parameters
        files = os.listdir(SEQS_DIR)
        if not files:
            display.show_fs_message("No existen archivos salvados")
            return
        self.stdscr.clear()
        self.stdscr.scrollok(True)
        self.stdscr.addstr(0, 5, "Seleccione el archivo. Presione 'q' para cancelar. ", curses.A_REVERSE)
        self.stdscr.move(1, 0)
        for file in files:
            self.stdscr.addstr("    " + file + "\n")
        self.stdscr.move(1, 0)
        self.stdscr.chgat(curses.A_REVERSE)
        while True:
            c = self.stdscr.getch()
            if c == curses.KEY_UP:
                y,x = self.stdscr.getyx()
                if y > 1:
                    self.stdscr.chgat(curses.A_NORMAL)
                    self.stdscr.move(y - 1, 0) 
                    self.stdscr.chgat(curses.A_REVERSE)
            elif c == curses.KEY_DOWN:
                y,x = self.stdscr.getyx()
                if y < self.stdscr.getmaxyx()[0] - 1:
                    self.stdscr.chgat(curses.A_NORMAL)
                    self.stdscr.move(y + 1, 0)
                    self.stdscr.chgat(curses.A_REVERSE)
            elif c == ord('q'):
                self.show_fs_message("Cancelado.")
                self.write_main_menu()
                return
            else:
                break
        y,x = self.stdscr.getmaxyx()
        name = self.stdscr.instr(x).strip()
        if not name:
            self.show_fs_message("Cancelado.")
            self. write_main_menu()
            return
        with open(SEQS_DIR + '/' + name, 'rb') as handle:
            out = pickle.loads(handle.read())
        
        parameters = out['parameters']
        note_lists = out['note_lists']
        self.show_fs_message("Archivo '%s' cargado"%name)
        self.stdscr.scrollok(False)

    def save_file(self):
        self.stdscr.clear()
        self.stdscr.addstr(3, 2, "Nombre del archivo: ")
        curses.echo()
        curses.curs_set(1)
        name = self.stdscr.getstr().strip()
        curses.noecho()
        curses.curs_set(0)
        if not name:
            self.show_fs_message("Cancelado")
            return
            
        if os.path.exists(SEQS_DIR + '/' + name):
            self.stdscr.addstr(5, 4, "Error, archivo ya existe!", curses.A_REVERSE)
            self.stdscr.addstr(6, 4, "Sobreescribir (S/N)?")
            self.stdscr.refresh()
            if self.stdscr.getch() != ord('s'):
                self.show_fs_message("Cancelado")
                self.write_main_menu()
                return
    
        with open(SEQS_DIR + '/' + name, 'wb') as handle:
            out = {'version': 1,
                   'note_lists': note_lists,
                   'parameters': parameters}
            pickle.dump(out, handle)
    
        self.stdscr.addstr(7, 4, "Archivo '%s' salvado"%name, curses.A_REVERSE)
        self.stdscr.refresh()
        time.sleep(2)
    
        self.write_main_menu()

    def write_sequencer(self):
        y,x = self.stdscr.getmaxyx()
        self.print_header(x,y)
    
        self.stdscr.addstr(3, 14, "Secuenciador - Pista %i"%cur_track,
                      curses.A_UNDERLINE | curses.A_BOLD)
        self.stdscr.addstr(5, 8, "1 - Editar")
        self.stdscr.addstr(6, 8, "2 - Reproducir pista")
        self.stdscr.addstr(7, 8, "3 - Reproducir todo")
        self.stdscr.addstr(8, 8, "4 - Programa")
        self.stdscr.addstr(9, 8, "5 - Cambiar pista")
        self.stdscr.addstr(10, 8, "6 - Cambiar Tempo (Actual: %f)"%tempo)
    
        self.stdscr.addstr(15, 8, "0 - Regresar")
        self.stdscr.refresh()    
    
    def run_sequencer(self):
        while True:
            self.write_sequencer()
            c = self.stdscr.getch()
            if c == ord('1'):
                self.make_text_editor()
            elif c == ord('2'):
                play_sequence(cur_track)
            elif c == ord('3'):
                play_sequence()
            elif c == ord('4'):
                self.run_program()
            elif c == ord('5'):
                self.change_track()
            elif c == ord('6'):
                self.change_tempo()
            elif c == ord('0'):
                break
            
    def make_text_editor(self):
        y,x = self.stdscr.getmaxyx()
        self.stdscr.addstr(y-2, 3, "Presione Ctrl+G para salir")
        #    curses.curs_set(1)
        editor = Editor(self.stdscr)
        editor.run_editor()
        
    def run_program(self):
        progs = os.listdir(PROG_DIR)
        for p in progs:
            if not p.endswith('.py'):
                progs.remove(p)
        while True:
            self.write_program_list(progs)
            c = self.stdscr.getkey()
            if c == '0':
                break
            if not c.isdigit():
                pass
            index = int(c) - 1
            if index < len(progs):
                run_prog(progs[index])
    
    def make_parameter_editor(self):
        y,x = self.stdscr.getmaxyx()
        self.print_header(x,y)
        self.stdscr.addstr(3, 14, "Parametros", curses.A_UNDERLINE | curses.A_BOLD)
    
        row = 5
        for key in parameters.keys():
            self.stdscr.addstr(row, 8, parameter_names[key] + ':' + str(parameters[key]))
            row = row + 1
            if row > y - 4:
                break
        self.stdscr.refresh()
        while True:
            c = self.stdscr.getch()
            if c == ord('0'): break  # Exit the while()
            elif c == ord('m'): break

    def write_program_list(self, progs):
        y, x = self.stdscr.getmaxyx()
        self.print_header(x,y)
    
        self.stdscr.addstr(3, 14, "Programas Heuristicos", curses.A_UNDERLINE | curses.A_BOLD)
        for i,prog in enumerate(progs):
            self.stdscr.addstr(i + 4, 8, "%i - %s"%(i+ 1, prog))
    
        self.stdscr.addstr(15, 8, "0 - Regresar")
        self.stdscr.refresh()
        
    def change_track(self):
        global cur_track
        y,x = self.stdscr.getmaxyx()
        self.print_header(x,y)
        curses.echo()
        self.stdscr.addstr(6, 4, 'Cambiar a pista: ')
        num = self.stdscr.getstr()
        curses.noecho()
        try:
            tr = int(num)
        except ValueError:
            self.show_fs_message('Entrada invalida!')
            return
        if not num.isdigit() or tr < 0 or tr > num_tracks:
            self.show_fs_message('Entrada invalida!')
            return
        cur_track = tr
        
    def change_tempo(self):
        global tempo
        y,x = self.stdscr.getmaxyx()
        self.print_header(x,y)
        curses.echo()
        self.stdscr.addstr(6, 4, 'Cambiar a tempo (Actual: %f): '%tempo)
        num = self.stdscr.getstr()
        curses.noecho()
        new_tempo = float(num)
        if new_tempo < 20 or new_tempo > 300:
            self.stdscr.addstr(10, 4, 'Entrada invalida!')
            self.stdscr.refresh()
            time.sleep(1)
            return
        tempo = new_tempo

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
            display.show_fs_message("Error compilando pista %i."%(cur_track))
            display.write_main_menu()
    else:
        for i in range(num_tracks):
            try:
                perf.InputMessage(convert_to_csound(note_lists[i]))
            except:
                display.show_fs_message("Error compilando pista %i."%(i))
                display.write_main_menu()
        

def run_prog(prog):
    try:
        line = "from %s import program"%(prog[:-3])
        exec(line)
        program(cur_track, note_lists, perf, display.stdscr)
    except Exception as e:
        display.show_fs_message("Error:" + str(e))
        


# This scrolling screen originally by Lyle Scott III
# lyle@digitalfoo.net
class Editor:
    def __init__(self, screen):
        self.topLineNum = 0
        self.highlightLineNum = 0
        
        self.SPACE_KEY = 32
        self.ESC_KEY = 27
        self.screen = screen
    
    def __del__(self):
        self.screen.bkgd(' ', curses.A_NORMAL)
        curses.curs_set(0)

    def run_editor(self):
        editwin = self.screen.subwin(curses.LINES, curses.COLS, 0, 0)
        editwin.clear()
        editwin.scrollok(True)
        self.topLineNum = 0
        self.highlightLineNum = 0
        curses.curs_set(0)
        while True:
            self.displayScreen()
            # get user command
            c = editwin.getch()
            nOutputLines = len(note_lists[cur_track].split('\n'))
            if c == curses.KEY_UP or c == ord('w'): 
                self.updown(-1, nOutputLines)
            elif c == curses.KEY_DOWN or c == ord('x'):
                self.updown(1, nOutputLines)
            elif c == curses.KEY_ENTER or c == ord('d'):
                self.addLine()
            elif  c == ord('j'):
                self.deleteLine()
            elif c == self.SPACE_KEY:
                self.editLine(editwin)
            elif c == ord('0') or c == ord('q'):
                break
        # editpad = Textbox(editwin)
        # note_lists[cur_track] = editpad.edit()
        # editwin.bkgd(' ', curses.A_NORMAL)
        # editwin.clear()
        #  curses.curs_set(0)
        del editwin

    def displayScreen(self):
        self.screen.clear()
        # now paint the rows
        bottom = self.topLineNum + curses.LINES -1
        lines = note_lists[cur_track].split('\n')
        self.screen.bkgd(' ', curses.A_REVERSE)
        for (index,line,) in enumerate(lines[self.topLineNum:bottom]):
            linenum = self.topLineNum + index
            line = '%04i %s' % (linenum + 1, line,)

            # highlight current line            
            if index != self.highlightLineNum:
                self.screen.addstr(index, 0, line, curses.A_REVERSE)
            else:
                self.screen.addstr(index, 0, line, curses.A_BOLD | curses.A_REVERSE)
    
        self.screen.move(self.highlightLineNum, 5)
        self.screen.refresh()
    
    
    def updown(self, increment, nOutputLines):
        nextLineNum = self.highlightLineNum + increment
    
        # paging
        if increment == -1 and self.highlightLineNum == 0 and self.topLineNum != 0:
            self.topLineNum += -1 
            return
        elif increment == 1 and nextLineNum == curses.LINES - 1 and (self.topLineNum+curses.LINES - 1) != nOutputLines:
            self.topLineNum += 1
            return
    
        # scroll highlight line
        if increment == -1 and (self.topLineNum != 0 or self.highlightLineNum != 0):
            self.highlightLineNum = nextLineNum
        elif increment == 1 and (self.topLineNum+self.highlightLineNum+1) != nOutputLines \
                and self.highlightLineNum != curses.LINES- 1:
            self.highlightLineNum = nextLineNum
    
    def addLine(self):
        lines = note_lists[cur_track].split('\n')
        lines.insert(self.highlightLineNum + 1, '')
        note_lists[cur_track] = '\n'.join(lines)
        nOutputLines = len(lines)
        self.updown(1, nOutputLines)
    
    def deleteLine(self):
        lines = note_lists[cur_track].split('\n')
        if len(lines) > 2: 
            lines.pop(self.highlightLineNum)
        if self.highlightLineNum >= len(lines):
            self.highlightLineNum -= 1
        note_lists[cur_track] = '\n'.join(lines)
    
    def editLine(self, editwin):
        lines = note_lists[cur_track].split('\n')
        linewin = editwin.subwin(1, curses.COLS - 5, self.highlightLineNum, 5)

        linewin.addstr(0, 0, lines[self.highlightLineNum])
        linewin.bkgd(' ')
        curses.curs_set(1)
        editpad = Textbox(linewin)
        new_line = editpad.edit()
        lines[self.highlightLineNum] = new_line
        note_lists[cur_track] = '\n'.join(lines)
        nOutputLines = len(note_lists[cur_track].split('\n'))
        self.updown(1, nOutputLines)
        curses.curs_set(0)


def key_pressed(text):
    freq = -220 + (ord(text[0])*10)
    perf.InputMessage("i 2 0 1 %f 100 1"%freq)

def main():
    global cs, perf, display
    init_data()
    sys.path.insert(0,PROG_DIR)
    
    display = Screen()

    display.show_initial_screen()

    init_arduino()
    if arduino is not None:
        display.append_text("Arduino inicializado.\n")
    else:
        display.append_text("Arduino no detectado\n")

    display.append_text("Iniciando Csound...")
    cs,perf = start_csound()

    for key in parameters.keys():
        cs.SetChannel(key, parameters[key])

    perf.Play()
    display.append_text("corriendo.\n")

    perf.InputMessage("i 2 0 0.3 440 100 1")
    perf.InputMessage("i 2 0.5 0.5 880 100 1")
    perf.InputMessage("i 2 1 0.5 220 100 1")
    perf.InputMessage("i 2 1.5 0.5 660 100 1")
    perf.InputMessage("i 2 2 2 110 100 1")

    time.sleep(4)
    display.main_menu()
    
    perf.Stop()
    if t is not None:
        t.stop()
    print "Finalizado.\n"
    display.cleanup()



if __name__ == "__main__":
    #time.sleep(1000)
    if not os.path.exists(SEQS_DIR):
        os.makedirs(SEQS_DIR)
    main()

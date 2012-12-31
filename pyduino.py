#! /usr/bin/env python

"""pyduino - A python library to interface with the firmata arduino firmware.
Copyright (C) 2007 Joe Turner <orphansandoligarchs@gmail.com>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

__version__ = "0.19_dev"

import time
import serial

# Message command bytes - straight outta Pd_firmware.pde
DIGITAL_MESSAGE = 0x90 # send data for a digital pin
ANALOG_MESSAGE = 0xE0 # send data for an analog pin (or PWM)

# PULSE_MESSAGE = 0xA0 # proposed pulseIn/Out message (SysEx)
# SHIFTOUT_MESSAGE = 0xB0 # proposed shiftOut message (SysEx)

REPORT_ANALOG_PIN = 0xC0 # enable analog input by pin #
REPORT_DIGITAL_PORTS = 0xD0 # enable digital input by port pair
START_SYSEX = 0xF0 # start a MIDI SysEx message
SET_DIGITAL_PIN_MODE = 0xF4 # set a digital pin to INPUT or OUTPUT
END_SYSEX = 0xF7 # end a MIDI SysEx message
REPORT_VERSION = 0xF9 # report firmware version
SYSTEM_RESET = 0xFF # reset from MIDI

# Pin modes
UNAVAILABLE = -1
DIGITAL_INPUT = 0
DIGITAL_OUTPUT = 1
DIGITAL_PWM = 2


PWM_PINS = (9, 10, 11)

class Arduino:
    """Base class for the arduino board"""

    def __init__(self, port):
        self.sp = serial.Serial(port, 115200, timeout=0.02)
        # Allow 2 secs for Diecimila auto-reset to happen
        time.sleep(2)

        self.analog = []
        for i in range(6):
            self.analog.append(AnalogPin(self.sp, i))

        self.digital_ports = []
        for i in range(2):
            self.digital_ports.append(DigitalPort(self.sp, i))

        # Don't mess with Rx/Tx
        self.digital_ports[0].pins[0].mode = UNAVAILABLE
        self.digital_ports[0].pins[1].mode = UNAVAILABLE
        # Pins 14 and 15 aren't used
        self.digital_ports[1].pins[6].mode = UNAVAILABLE
        self.digital_ports[1].pins[7].mode = UNAVAILABLE

        # Syntactic sugar - don't make the end user mess with ports too much
        # and keep the api stable-ish
        self.digital = []
        self.digital += self.digital_ports[0].pins
        # Leave out pins 14 and 15 so the length matches the board
        self.digital += self.digital_ports[1].pins[:6]
        
        # Obtain firmata version
        self.firmata_version = None
        self.sp.write(chr(REPORT_VERSION))
        self.iterate()

    def __str__(self):
        return "Arduino: %s"% self.sp.port
            
    def iterate(self):
        """Read and handle a command byte from Arduino's serial port"""
        data = self.sp.read()
        if data != "":
            self._process_input(ord(data))

    def _process_input(self, data):
        """Process a command byte and any additional information bytes"""
        if data < 0xF0:
            #Multibyte
            message = data & 0xF0
            if message == DIGITAL_MESSAGE:
                port_number = data & 0x0F
                #Digital in
                lsb = ""
                msb = ""
                while lsb == "":
                    lsb = self.sp.read()
                while msb == "":
                    msb = self.sp.read()
                lsb = ord(lsb)
                msb = ord(msb)
                print port_number
                self.digital_ports[port_number].set_value(msb << 7 | lsb)
            elif message == ANALOG_MESSAGE:
                pin_number = data & 0x0F
                #Analog in
                lsb = ""
                msb = ""
                while lsb == "":
                    lsb = self.sp.read()
                while msb == "":
                    msb = self.sp.read()
                lsb = ord(lsb)
                msb = ord(msb)
                value = float(msb << 7 | lsb) / 1023
                self.analog[pin_number].set_value(value)
        elif data == REPORT_VERSION:
            minor, major = self.sp.read(2)
            self.firmata_version = (ord(major), ord(minor))

    def get_firmata_version(self):
        """Return a (major, minor) version tuple for the firmata firmware"""
        return self.firmata_version

    def exit(self):
        """Exit the application cleanly"""
        self.sp.close()

class DigitalPort:
    """Digital pin on the arduino board"""
    def __init__(self, sp, port_number):
        self.sp = sp
        self.port_number = port_number
        self.is_active = 0

        self.pins = []
        for i in range(8):
            self.pins.append(DigitalPin(sp, self, i))

    def __str__(self):
        return "Digital Port %i"% self.port_number

    def set_active(self, active):
        """ Set the port to report values """
        self.is_active = active
        message = chr(REPORT_DIGITAL_PORTS + self.port_number)
        message += chr(active)
        self.sp.write(message)

    def get_active(self):
        """Return whether the port is reporting values"""
        return self.is_active

    def set_value(self, mask):
        """Record the value of each of the input pins belonging to the port"""

        for pin in self.pins:
            if pin.mode == DIGITAL_INPUT:
                pin.set_value((mask & (1 << pin.pin_number)) > 1)

    def write(self):
        """Set the output pins of the port to the correct state"""
        mask = 0
        for pin in self.pins:
            if pin.mode == DIGITAL_OUTPUT:
                if pin.value == 1:
                    mask |= 1 << pin.pin_number
        message = chr(DIGITAL_MESSAGE + self.port_number)
        message += chr(mask % 128)
        message += chr(mask >> 7)
        self.sp.write(message)

class DigitalPin:
    """Digital pin on the arduino board"""

    def __init__(self, sp, port, pin_number):
        self.sp = sp
        self.port = port
        self.pin_number = pin_number
        self.value = 0
        self.mode = DIGITAL_INPUT

    def __str__(self):
        return "Digital Pin %i"% self.pin_number

    def set_mode(self, mode):
        """Set the mode of operation for the pin
        
        Argument:
        mode, takes a value of: - DIGITAL_INPUT
                                - DIGITAL_OUTPUT
                                - DIGITAL_PWM

        """
        if (mode == DIGITAL_PWM and
           self._get_board_pin_number() not in PWM_PINS):
            error_message = "Digital pin %i does not have PWM capabilities" \
                            % (self._get_board_pin_number())
            raise IOError, error_message
        if self.mode == UNAVAILABLE:
            raise IOError, "Cannot set mode for pin %i" \
                           % (self._get_board_pin_number())
        self.mode = mode
        command = chr(SET_DIGITAL_PIN_MODE)
        command += chr(self._get_board_pin_number())
        command += chr(mode)
        self.sp.write(command)

    def get_mode(self):
        """Return the pin mode, values explained in set_mode()"""
        return self.mode

    def _get_board_pin_number(self):
        """Return the number of the pin as written on the board"""
        return (self.port.port_number * 8) + self.pin_number

    def set_value(self, value):
        """Record the value of the pin"""
        self.value = value

    def read(self):
        """Return the output value of the pin, values explained in write()"""
        if self.mode == UNAVAILABLE:
            raise IOError, "Cannot read pin %i"% self._get_board_pin_number()
        return self.value

    def write(self, value):
        """Output a voltage from the pin

        Argument:
        value, takes a boolean if the pin is in output mode, or a float from 0
        to 1 if the pin is in PWM mode

        """
        if self.mode == UNAVAILABLE:
            raise IOError, "Cannot read from pin %i" \
                           % (self._get_board_pin_number())
        if self.mode == DIGITAL_INPUT:
            raise IOError, "Digital pin %i is not an output" \
                            % (self._get_board_pin_number())
        elif value != self.read():
            self.value = value
            if self.mode == DIGITAL_OUTPUT:
                self.port.write()
            elif self.mode == DIGITAL_PWM:
                value = int(round(value * 255))
                message = chr(ANALOG_MESSAGE + self._get_board_pin_number())
                message += chr(value % 128)
                message += chr(value >> 7)
                self.sp.write(message)


class AnalogPin:
    """Analog pin on the arduino board"""

    def __init__(self, sp, pin_number):
        self.sp = sp
        self.pin_number = pin_number
        self.active = 0
        self.value = -1

    def __str__(self):
        return "Analog Input %i"% self.pin_number

    def set_active(self, active):
        """Set the pin to report values"""
        self.active = active
        message = chr(REPORT_ANALOG_PIN + self.pin_number)
        message += chr(active)
        self.sp.write(message)

    def get_active(self):
        """Return whether the pin is reporting values"""
        return self.active

    def set_value(self, value):
        """Record the value of the pin"""
        self.value = value

    def read(self):
        """Return the input in the range 0-1"""
        return self.value

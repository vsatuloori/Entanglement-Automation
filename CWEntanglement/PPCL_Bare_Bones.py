import pyvisa
import numpy as np
import time
import yaml

from Support.LaserSupport.PPCL550v7_linux import PPCL550

class LaserControl:
    def __init__(self, filename=None, settings=None, port=None, baud_rate=9600, min_pow=600, max_pow=1700, wavelength=1550, power=6):
        if (filename):
            with open(filename, 'r') as yaml_file:
                settings = yaml.safe_load(yaml_file)
        
        if (settings):
            port = settings["port"]
            baud_rate = settings["baud_rate"]
            min_pow = settings["min_pow"]
            max_pow = settings["max_pow"]
            wavelength = settings["wavelength"]
            power = settings["power"]
        
        self.laser = PPCL550(port, baud_rate, min_pow=min_pow, max_pow=max_pow)
        self.rm = pyvisa.ResourceManager()
        self.C = 299792458  # Speed of light in m/s
        self.wl = wavelength
        self.power = power
        self.dev = None

    def connect_laser(self):  # power in dBm
        try:
            print("wd")
            self.dev = self.laser.connect_laser()
            freq = np.round(self.C / self.wl * 1e-3, 3)
            print(self.dev)
            time.sleep(0.001)
            print(self.laser.NOP_register())
            failures = 0
            while not self.laser.is_NOP_correct() or not self.laser.write_freq(freq):
                print("Laser reconnecting...")
                self.turn_off()
                self.laser.disconnect_laser()
                time.sleep(1)
                self.dev = self.laser.connect_laser()
                failures += 1
                if failures >= 10:
                    raise self.laser.NOPException("NOP register gave the wrong result 10 times, check device connection")
                time.sleep(0.01)
                print(self.laser.NOP_register())
            time.sleep(0.001)
            print(self.laser.write_power(self.power * 100))
            time.sleep(0.001)
            print(self.laser.write_freq(freq))
            time.sleep(0.001)
        except Exception as error:
            print(f"Connection to laser failed. Error: {error}")
            self.dev = None

    def turn_on(self, wait_time=1):
        try:
            self.laser.laser_on()
            for i in range(wait_time, 0, -1):
                print(f"Turning laser on... wait for {i} seconds", end="\r")
                time.sleep(1)
        except Exception as error:
            print(f'Turning laser on failed. Error: {error}')

    def turn_off(self):
        try:
            self.laser.laser_off()
        except Exception as error:
            print(f'Turning laser off failed. Error: {error}')

    def disconnect(self):
        try:
            if self.dev != None:
                self.laser.disconnect_laser()
                print("Laser is disconnected")
                self.dev = None
        except Exception as error:
            print(f"Unable to disconnect laser. Error: {error}")


if __name__ == "__main__":
    # ports = ["COM3", "COM14"]
    port = "/dev/ttyUSB1"
    laser1= LaserControl(port=port, wavelength=1535.82)
    print(laser1)
    # LaserControl(port=port)
    # laser.disconnect()
    laser1.connect_laser()
    laser1.turn_on()
    # laser1.laser.write_power(600)
    # laser1.turn_off()
    # laser1.turn_off()
    # laser.laser.laser_on()
    # laser.laser.read_freq()
    # laser.laser.write_freq(193.4)
    # laser.laser.read_freq()
    
    #laser.turn_on()
    # for port in ports:
    #     laser = LaserControl(port=port)
    #     # laser.disconnect()
    #     laser.connect_laser()
    #     laser.turn_on(wait_time=3)
    #     # laser.turn_off()
    #     # laser.disconnect()
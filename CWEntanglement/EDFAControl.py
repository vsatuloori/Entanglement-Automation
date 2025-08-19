import sys
import os
import csv
import yaml
from time import sleep
from datetime import datetime
#import DBCtrl
import serial
import time
import re
"""
EDFA control
"""

class EDFAControl: 
    def __init__(self, params=None, filename = None, port=None, baud_rate=9600):
        self.ser = serial.Serial()
        if filename:
            with open(filename, 'r') as yaml_file:
                settings = yaml.safe_load(yaml_file)
            # Iterate through Alice, Bob, Charlie and find EDFA controls
            found = False
            for name in ["Alice", "Bob", "Charlie"]:
                if name in settings and "EDFA" in settings[name]:
                    edfa_params = settings[name]["EDFA"]
                    self.ser.port = edfa_params.get("port", port)
                    self.ser.baudrate = edfa_params.get("baud_rate", baud_rate)
                    self.current = int(edfa_params.get("pump_current", 0))
                    self.min_cur = float(edfa_params.get("min_cur", 0))
                    self.max_cur = float(edfa_params.get("max_cur", 890))
                    found = True
                    break  # Remove this if you want to process all found EDFAs
            if not found:
                # Fallback defaults if no EDFA found
                self.current = 0
                self.port = port
                self.baud_rate = baud_rate
                self.min_cur = 0
                self.max_cur = 890
                self.ser.port = port
                self.ser.baudrate = baud_rate
        elif (params):
            # edfa_params = settings[name]["EDFA"]
            self.ser.port = params.get("port", port)
            self.ser.baudrate = params.get("baud_rate", baud_rate)
            self.current = int(params.get("pump_current", 0))
            self.min_cur = float(params.get("min_cur", 0))
            self.max_cur = float(params.get("max_cur", 890))
            found = True
        else:
            self.current = 0
            self.port = port
            self.baud_rate = baud_rate
            self.min_cur = 0
            self.max_cur = 890
            self.ser.port = port
            self.ser.baudrate = baud_rate
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.rtscts = 0
        self.ser.dsrdtr = 0
        self.ser.xonxoff = 0
        self.ser.stopbits = 1
        self.ser.timeout = 1
        self.step_size = 10


    def send_command(self, cmd):
        cmd = cmd+"\r\n"
        self.ser.write(cmd.encode())

    def get_response(self):
        response = ""
        for i in range(3):
            value = self.ser.readline().strip().decode()
            response+=value
        return response
    def connect(self, set = False):
        try:
            self.ser.open()
            if self.ser.is_open:
                print("Serial port opened successfully.")
                self.send_command("READY?")
                print(self.get_response())
                self.pump_on()
                if set:
                    self.set_current(f"{self.current:04d}")  # Format current with leading zeroes
            else:
                print("Failed to open serial port.")
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            sys.exit(1)
    def pump_on(self):
        self.send_command("FA ON")
        response = self.get_response()
        print(response)
        return response
    def pump_off(self):
        self.send_command("FA OFF")
        response = self.get_response()
        print(response)
        return response
    # def set_current(self, current): # include leading zeroes, e.g. 0365
    #     current = int(current)
    #     self.step_size = 5
    #     if not (self.min_cur <= int(current) <= self.max_cur):
    #         raise ValueError(f"Current must be between {self.min_cur} and {self.max_cur}.")
    #     curr_current= int(self.get_current()) 
    #     while (abs(current - curr_current) > 10):
    #         if current > curr_current:
    #             self.send_command(f"FA SET {(curr_current+self.step_size):04d}")
    #         else:
    #             self.send_command(f"FA SET {(curr_current-self.step_size):04d}")
    #         curr_current = self.get_current()
    #         print(f"Current set to {curr_current} mA")
    #         # time.sleep(0.1)
    #     self.send_command(f"FA SET {current:04d}")
    #     # response = self.get_response()
    #     # print(response)
    #     return f"Current set to {current} mA"

    def set_current(self, current):
        current = int(current)
        self.step_size = 5
        max_steps = 100  # safety limit to avoid infinite loops

        if not (self.min_cur <= current <= self.max_cur):
            raise ValueError(f"Current must be between {self.min_cur} and {self.max_cur}.")

        try:
            curr_current = int(self.get_current())
        except Exception as e:
            return f"Error reading current: {e}"

        step_count = 0
        while abs(current - curr_current) > 10 and step_count < max_steps:
            step_count += 1
            next_val = curr_current + self.step_size if current > curr_current else curr_current - self.step_size
            self.send_command(f"FA SET {next_val:04d}")
            try:
                curr_current = int(self.get_current())
            except Exception as e:
                return f"Error reading current during stepping: {e}"
            print(f"Current stepped to {curr_current} mA")

        # Final set
        self.send_command(f"FA SET {current:04d}")
        try:
            final_current = int(self.get_current())
        except Exception as e:
            return f"Final set failed: {e}"
        
        return f"Current set to {final_current} mA"

    def get_current(self):
        self.send_command("FA P1CUR?")
        response = self.get_response()
        # print(response)
        match = re.search(r'\d+', response)
        if match:
            act_current = int(match.group())
            # print(f"pump_current = {act_current}mA")
            return act_current
        else:
            print("No integer found in response.")
            return None



#Sometimes this script works only after originally typing these serial commands directly using minicom. I'm not sure exactly why. Open minicom using sudo minicom -s. Default settings seem to work.
# ser.open()
# if ser.is_open:
#      print("Serial Open")
#      send_command(ser,"READY?")
#      print(get_response(ser))
#      send_command(ser,"FA ON")
#      print(get_response(ser))
    #  send_command(ser,"FA OFF")
    #  print(get_response(ser))


if __name__ == "__main__":
    edfa = EDFAControl(filename = "./CWEntanglement/EDFAControl.yaml")
    edfa.connect()
    edfa.set_current(f"{edfa.current:04d}")
    print(edfa.get_current())
    edfa.set_current(f"{0:04d}")
    
    # edfa.send_command("FA SET 0040")
    # time.sleep(1)
    # edfa.pump_on()
    # edfa.get_current()
    # edfa.set_current("70")  # Example current setting
    # start_time = time.time()
    # for i in range(10):
    #     edfa.get_current()
    # print(f"time taken:{time.time() - start_time} seconds  ")
    # edfa.set_current("0180")  # Change current as needed

# send_command(ser,"FA SET "+ "0365")
# print(get_response(ser))



# """
# Sweep through voltages and currents.
# """

# edfa_currents = ["0140","0215","0290","0365","0440","0515","0590","0665","0740","0815","0890"]
# wait_time=300

# print("total time (hours): ", len(edfa_currents)*wait_time/3600)

# start_time = datetime.now()
# for j in range(len(edfa_currents)):
#     print(" ")
#     edfa_curr = edfa_currents[j]
#     send_command(ser,"FA OFF")
#     print(get_response(ser))
#     send_command(ser,"FA SET "+edfa_curr)
#     print(get_response(ser))
#     send_command(ser,"FA ON")
#     print(get_response(ser))
#     now = datetime.now()
#     data = [now, (now-start_time).total_seconds()]
#     print('start time: {} |total time: {}'.format(data[0], data[1]))
#     now = datetime.now()
#     sleep(wait_time)
#     print("end time: ", now, "total time: ", (now-start_time).total_seconds())
#     print("")
# ser.close()

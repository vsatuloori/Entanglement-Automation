import serial
import time
import numpy as np
from multiprocessing import Process
import yaml
start_time = time.time()

class OpticalSwitchDriver:
    def __init__(self, params, baudrate=9600, timeout=0.5, filename = None):
        self.com_port = params["com_port"]
        self.baudrate = baudrate
        self.timeout = timeout
        self.minvoltage = 0
        self.amplification = 4
        self.maxvoltage = 4.9
        self.device_connected = False
        self.device = None
        if self.com_port != None:
            self.load_osw_settings(params)
    
    
    def load_osw_settings(self, params):
        """Load the OSW settings from the YAML file."""
            # Access OSW switch statuses
        self.SW1Status = None
        self.SW2Status = None
        self.SW3Status = None
        self.SW4Status = None
        try:
            if params is None:
                print(f"Params not mentioned to load OSW settings")
            else:
                # with open(filename, 'r') as file:
                #     data = yaml.safe_load(file)

                # Set OSW statuses from the file
                self.SW1Status = params['SW1']
                self.SW2Status = params['SW2']
                self.SW3Status = params['SW3']
                self.SW4Status = params['SW4']

                # Set all switches based on the loaded configuration
                self.OSWAll([self.SW1Status, self.SW2Status, self.SW3Status, self.SW4Status], sleep_time=0.1)

                print(f"OSW settings applied: SW1={self.SW1Status}, SW2={self.SW2Status}, SW3={self.SW3Status}, SW4={self.SW4Status}")

        except Exception as e:
            print(f"Error loading OSW settings: {e}")   

    def connect(self):
        if self.com_port == None:
            print(f"OSW com port is :{self.com_port}")
        else:
            if not self.device_connected or self.device==None: 
                print("OSW is not connected. Connecting now...")
                try:
                    self.device = serial.Serial(port=self.com_port, baudrate=self.baudrate, timeout=self.timeout)
                    self.device_connected = True
                    print("OSW is connected")
                    time.sleep(2)  # Give some time for the device to initialize
                except serial.SerialException as e:
                    print(f"Failed to connect to OSW: {e}")
                    self.device = None
            else:
                print("OSW is already connected.")
            return self.device
    
    def OSWAll(self, statuses, sleep_time):
        try:
            if not self.device_connected:
                print("OSW is not initialized, attempting to connect...")
                self.device = self.connect()

            if self.device is None:
                raise RuntimeError("Failed to connect to the OSW or OSW not initialized")

            for channel, status in enumerate(statuses):
                command = f"DF2X2 {channel} {status}\n"
                start_time = time.time()
                self._send_command(command, start_time)
                time.sleep(sleep_time)

        except Exception as e:
            print(e)
            print("Could not set the optical switches")

    def OSWch(self, channel, status):
        try:
            if not self.device_connected:
                print("OSW not initialized, attempting to connect...")
                self.device = self.connect()

            if self.device is None:
                raise RuntimeError("Failed to connect to the OSW or OSW not initialized")

            command = f"DF2X2 {channel} {status}\n"
            start_time = time.time()
            self._send_command(command, start_time)
        except Exception as e:
            print(e)
            print("Could not set the voltage")
        
     
    def _send_command(self, command, start_time):
        print(command)
        # self.device.write(bytes(command, 'utf-8'))
        # while True:
        #     data = self.device.readline()
        #     dataStr = data.decode().strip()
        #     if dataStr == "+ok":
        #         # print(f" Applied voltage {self.amplification*float(command.split()[2])}V, Command:{command.strip()}, running time: {time.time() - start_time:.5f}s")
        #         break
        #     else:
        #         print(f"Received data: {dataStr}")
        #         print(f"Data not received and running time: {time.time() - start_time:.5f} seconds")
        #         break
    def disconnect(self):
        print("OSW disconnects automatically")

if __name__ == "__main__":
   OSW = OpticalSwitchDriver(com_port=None)
   OSW.device = OSW.connect()
   IntAVoltage = 0 #Ch1
   IntBVoltage = 0 #Ch2
   IntCVoltage = 0 #Ch3
   IntDVoltage = 0 #Ch4
   OSW.disconnect()
#    for IntDVoltage in np.arange(0,5,0.1):
#     #    InterferometerVSrc.Vset([IntDVoltage, IntCVoltage, IntBVoltage, IntAVoltage], sleep_time=0.1)
#        InterferometerVSrc.Vset([IntDVoltage, IntDVoltage, IntDVoltage, IntDVoltage], sleep_time=0.1)
#        time.sleep(1)
                                                                                      



                                             
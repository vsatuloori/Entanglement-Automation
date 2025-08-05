import serial
import time
import numpy as np
from multiprocessing import Process
start_time = time.time()

class LADAqBoard:
    def __init__(self, com_port, baudrate=9600, timeout=0.5):
        self.com_port = com_port
        self.baudrate = baudrate
        self.timeout = timeout
        self.minvoltage = 0
        self.amplification = 2
        self.maxvoltage = 4.9#
        self.device_connected = False
        self.device = self.connect()

    # def is_device_connected(self):
    #     try:
    #         ser = serial.Serial(self.com_port)
    #         ser.close()
    #         return True
    #     except serial.SerialException:
    #         return False
        
    def connect(self):
        # if not self.is_device_connected():
        if not self.device_connected or self.device==None: 
            print("LADAq is not connected. Connecting now...")
            try:
                self.device = serial.Serial(port=self.com_port, baudrate=self.baudrate, timeout=self.timeout)
                self.device_connected = True
                print("LADAq is connected")
                time.sleep(0.1)  # Give some time for the device to initialize
            except serial.SerialException as e:
                print(f"Failed to connect to LADAq: {e}")
                self.device = None
        else:
            print("LADAq is already connected.")
        return self.device
    
    def Vset(self, voltages, sleep_time=0.01):
        try:
            if not self.device_connected:
                print("LADAq not initialized, attempting to connect...")
                self.device = self.connect()

            if self.device is None:
                raise RuntimeError("Failed to connect to the LADAq or LADAq not initialized")

            for channel, volt in enumerate(voltages):
                if volt<=self.maxvoltage:
                    DACvoltage = volt/self.amplification # This is to ensure that volt is in between 0 and self.maxvoltage/amplification factor
                    command = f"Vset {channel} {DACvoltage}\n"
                    start_time = time.time()
                    self._send_command(command, start_time)
                    time.sleep(sleep_time)
                else:
                    print(f"Voltage set to channel {channel} is {volt}V exceeds the maximum limit of {self.maxvoltage}V \n Not changing the previous voltage") 


        except Exception as e:
            print(e)
            print("Could not set the voltage")

    def VsetCh(self, voltage, channel):
        try:
            if not self.device_connected:
                print("LADAq not initialized, attempting to connect...")
                self.device = self.connect()

            if self.device is None:
                raise RuntimeError("Failed to connect to the LADAq or LADAq not initialized")

            if voltage<=self.maxvoltage:
                DACvoltage = voltage/self.amplification # This is to ensure that volt is in between 0 and self.maxvoltage/amplification factor
                command = f"Vset {channel} {DACvoltage}\n"
                start_time = time.time()
                self._send_command(command, start_time)
            else:
                print(f"Voltage set to channel {channel} is {voltage}V exceeds the maximum limit of {self.maxvoltage}V \n Not changing the previous voltage") 
            

        except Exception as e:
            print(e)
            print("Could not set the voltage")
        
    def VsAll(self, channel_list, voltage_list):
        """Set multiple channels at once using VsAll command."""
        try:
            if not self.device_connected:
                print("LADAq not initialized, attempting to connect...")
                self.device = self.connect()

            if self.device is None:
                raise RuntimeError("Failed to connect to the LADAq or LADAq not initialized")

            if len(channel_list) != len(voltage_list):
                raise ValueError("channel_list and voltage_list must have the same length")

            voltages_to_send = []
            for volt in voltage_list:
                if volt <= self.maxvoltage:
                    DACvoltage = volt / self.amplification
                    voltages_to_send.append(str(DACvoltage))
                else:
                    raise ValueError(f"Voltage {volt}V exceeds maximum allowed {self.maxvoltage}V")

            command = "VsAll " + " ".join(voltages_to_send) + "\n"
            start_time = time.time()
            self._send_command(command, start_time)

        except Exception as e:
            print(e)
            print("Could not set voltages using VsAll")

    def _send_command(self, command, start_time):
        self.device.write(bytes(command, 'utf-8'))
        while True:
            data = self.device.readline()
            dataStr = data.decode().strip()
            if dataStr == "+ok":
                # print(f" Applied voltage {self.amplification*float(command.split()[2])}V, Command:{command.strip()}, running time: {time.time() - start_time:.5f}s")
                break
            else:
                print(f"Received data: {dataStr}")
                print(f"Data not received and running time: {time.time() - start_time:.5f} seconds")
                break
    def disconnect(self):
        print("LADAq disconnects automatically")

if __name__ == "__main__":
   InterferometerVSrc = LADAqBoard("/dev/ttyACM2")
   InterferometerVSrc.device = InterferometerVSrc.connect()
   IntAVoltage = 1.148 #Ch1
   IntBVoltage = 0.6  #Ch2
   IntCVoltage = 0.5  #Ch3
   IntDVoltage = 0.1  #Ch4
   InterferometerVSrc.Vset([IntDVoltage, IntCVoltage, IntBVoltage, IntAVoltage], sleep_time=0.1)
#    for IntDVoltage in np.arange(0,5,0.1):
#     #    InterferometerVSrc.Vset([IntDVoltage, IntCVoltage, IntBVoltage, IntAVoltage], sleep_time=0.1)
#        InterferometerVSrc.Vset([IntDVoltage, IntDVoltage, IntDVoltage, IntDVoltage], sleep_time=0.1)
#        time.sleep(1)
                                                                                      



                                             
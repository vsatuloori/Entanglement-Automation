import pyvisa
import usbtmc
import time
import re
from ThorlabsPM100 import ThorlabsPM100

class PowerMeter:
    def __init__(self, power_meter_id='USB0::0x1313::0x8078::P0023583::INSTR', wavelength=1536, use_pyvisa=True):
        """Initialize the Thorlabs Power Meter using a single power_meter_id."""
        self.use_pyvisa = use_pyvisa
        self.power_meter_id = power_meter_id

        if self.power_meter_id is None:  # <<< Handle None case
            print("PowerMeter ID is None. Skipping power meter initialization.")
            self.device = None
            self.power_meter = None
            self.connected = False
            return  # Exit initialization early

        # Automatically extract vendor_id and product_id
        match = re.search(r'USB0::0x([0-9A-Fa-f]+)::0x([0-9A-Fa-f]+)::', power_meter_id)
        if not match:
            raise ValueError("Failed to extract vendor_id and product_id from power_meter_id.")

        vendor_id_usbtmc = int(match.group(1), 16)
        product_id_usbtmc = int(match.group(2), 16)

        try:
            if self.use_pyvisa:
                self.rm = pyvisa.ResourceManager()
                self.device = self.rm.open_resource(power_meter_id)
                self.power_meter = ThorlabsPM100(inst=self.device)
            else:
                self.device = usbtmc.Instrument(vendor_id_usbtmc, product_id_usbtmc)
                self.power_meter = ThorlabsPM100(inst=self.device)

            self.connected = True
            self.set_wavelength(wavelength)
            time.sleep(1)  # Let wavelength setting settle
            self.confirm_connection()

        except Exception as e:
            print(f"Failed to initialize PowerMeter: {e}")
            self.device = None
            self.power_meter = None
            self.connected = False

    def set_wavelength(self, wavelength):
        if self.device is None:
            print("No device connected. Cannot set wavelength.")  # <<< safe guard
            return
        print(f"Setting wavelength to {wavelength} nm.")
        self._send_command(f"SENS:CORR:WAV {wavelength}NM")

    def confirm_connection(self):
        if self.device is None:
            print("No device connected. Skipping confirmation.")  # <<< safe guard
            return
        response = self._query_command("*IDN?")
        print(f"Connected to: {response}")

    def measure_power(self, N=1, delay=0.01):
        if self.device is None:
            print("No device connected. Returning empty power list.")  # <<< safe guard
            return []
        
        powers = []
        for i in range(N):
            retries = 0
            while retries < 5:
                try:
                    power = self._query_command("MEAS:POW?")
                    powers.append(float(power))
                    break
                except Exception as e:
                    retries += 1
                    print(f"Error reading power (attempt {retries}/5): {e}")
        return powers

    def _send_command(self, command):
        if self.device:
            self.device.write(command)

    def _query_command(self, command):
        if self.device is None:
            raise ConnectionError("Device not connected.")
        
        if self.use_pyvisa:
            return self.device.query(command)
        else:
            return self.device.ask(command)

# Example usage
if __name__ == "__main__":
    # Initialize the Thorlabs Power Meter with pyvisa or usbtmc depending on the use_pyvisa flag
    use_pyvisa = True  # Set to True to use pyvisa, or False to use usbtmc

    power_meter_id = 'USB0::0x1313::0x8078::P0023583::INSTR'
    if use_pyvisa:
        power_meter = PowerMeter(power_meter_id=power_meter_id, wavelength=1536, use_pyvisa=True)
    else:
        power_meter = PowerMeter(power_meter_id=power_meter_id, wavelength=1536, use_pyvisa=False)

    # Measure the power
    measured_power = power_meter.measure_power(N=10)
    print(f"Measured Power Samples: {measured_power}")

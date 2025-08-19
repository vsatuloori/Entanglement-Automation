import nidaqmx
from nidaqmx.constants import TerminalConfiguration, Edge, AcquisitionType, VoltageUnits
import numpy as np
import time
from datetime import datetime

class NIDAQ_USB:
    def __init__(self, devID, ai_samples, ai_rate, ai_channels, incr=1,
                 ao_samples=None, ao_rate=None, ao_channels=1, min_v=0, max_v=1.5):
        """
        Initializes NIDAQ USB device for Analog Input (AI) and Analog Output (AO).

        Arguments:
        devID: Device identifier (e.g., 'Dev1').
        ai_samples: Total number of AI samples per collection run.
        ai_rate: AI sampling rate.
        ai_channels: Number of AI channels.
        incr: Number of AI samples per increment (default: 1).

        Optional:
        ao_samples: Total number of AO samples (default: None).
        ao_rate: AO sampling rate (default: None).
        ao_channels: Number of AO channels (default: 1).
        min_v, max_v: Voltage range for AO channels.
        """
        self.devID = devID
        self.ai_samples = int(ai_samples)
        self.ai_rate = ai_rate
        self.ai_channels = ai_channels
        self.incr = incr
        
        self.ao_samples = ao_samples
        self.ao_rate = ao_rate
        self.ao_channels = ao_channels
        self.min_v = min_v
        self.max_v = max_v

        self.ai_task = None
        self.ao_task = None

        self.data = {
            "AI Data": np.zeros((ai_channels + 1, ai_samples)),
            "AO Data": np.zeros((ao_channels + 1, ao_samples if ao_samples else 0))
        }

    def __str__(self):
        return (f"<NIDAQ_USB: {self.devID}>\n"
                f"AI - Samples: {self.ai_samples}, Rate: {self.ai_rate}, Channels: {self.ai_channels}\n"
                f"AO - Samples: {self.ao_samples}, Rate: {self.ao_rate}, Channels: {self.ao_channels}")

    # Setup Functions
    def setup_ai_task(self):
        """Setup Analog Input task."""
        self.ai_task = nidaqmx.Task()
        self.ai_task.ai_channels.add_ai_voltage_chan(
            f"{self.devID}/ai0:{self.ai_channels - 1}",
            terminal_config=TerminalConfiguration.RSE
        )
        self.ai_task.timing.cfg_samp_clk_timing(
            rate=self.ai_rate,
            sample_mode=AcquisitionType.FINITE,
            samps_per_chan=self.ai_samples
        )

    def setup_ao_task(self):
        """Setup Analog Output task."""
        if not self.ao_samples or not self.ao_rate:
            raise ValueError("AO samples and rate must be defined for AO task.")

        self.ao_task = nidaqmx.Task()
        self.ao_task.ao_channels.add_ao_voltage_chan(
            f"{self.devID}/ao0:{self.ao_channels - 1}",
            min_val=self.min_v, max_val=self.max_v
        )
        self.ao_task.timing.cfg_samp_clk_timing(
            rate=self.ao_rate,
            sample_mode=AcquisitionType.FINITE,
            samps_per_chan=self.ao_samples
        )

    # Task Control Functions
    def start_task(self, task):
        if task:
            task.start()

    def stop_task(self, task):
        if task:
            task.stop()

    def close_task(self, task):
        if task:
            task.close()

    def close_all_tasks(self):
        self.close_task(self.ai_task)
        self.close_task(self.ao_task)

    # Measurement Functions
    def ai_measurement(self):
        """Perform a single AI measurement."""
        if not self.ai_task:
            raise RuntimeError("AI task not set up. Call setup_ai_task() first.")

        data_values = np.zeros((self.ai_channels + 1, self.ai_samples))
        ai_start = time.perf_counter()

        self.start_task(self.ai_task)
        data_read = self.ai_task.read(number_of_samples_per_channel=self.ai_samples)
        self.stop_task(self.ai_task)

        data_values[1:, :] = np.array(data_read)
        data_values[0, :] = time.perf_counter() - ai_start

        return data_values

    def ao_output(self, data):
        """Send data to AO channels."""
        if not self.ao_task:
            raise RuntimeError("AO task not set up. Call setup_ao_task() first.")
        if len(data) != self.ao_samples:
            raise ValueError("AO data size must match ao_samples.")

        self.ao_task.write(data, auto_start=False)
        self.start_task(self.ao_task)
        self.stop_task(self.ao_task)

    # Data Handling Functions
    def save_data(self, filename):
        """Save AI data to a file."""
        np.savez(filename, **self.data)
        print(f"Data saved to {filename}")

    def load_data(self, filename):
        """Load data from a file."""
        self.data = np.load(filename)
        print(f"Data loaded from {filename}")

# Example usage (Replace with actual device parameters)
if __name__ == "__main__":
    device = NIDAQ_USB(
        devID="Dev1",
        ai_samples=10000,  # Number of samples per channel
        ai_rate=10000,     # Sampling rate in Hz
        ai_channels=4      # Channels 1-4
    )

    print(device)

    try:
        # Setup the AI task
        device.setup_ai_task()

        # Perform data acquisition
        ai_data = device.ai_measurement()

        # Process and print results
        print(f"AI Measurement Data (Channels 1-4):\n{ai_data}")

        # Save data if needed
        device.save_data(f"AI_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.npz")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        device.close_all_tasks()

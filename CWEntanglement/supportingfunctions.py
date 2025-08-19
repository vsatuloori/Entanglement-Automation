import matplotlib.pyplot as plt
import numpy as np
import os
import time 
import re


class SupportFunc:

    def find_extrema(self, voltage_power_data, tolerance=0.05):
        """Finds voltages corresponding to minimum power, maximum power, and (min + max) / 2.
        Groups and averages voltages within a 0.2V range and returns them in ascending order."""
        voltages, powers = zip(*voltage_power_data)

        # Flatten the powers list if it contains lists within
        flat_powers = (powers)

        # Find the actual min and max power values
        min_power = min(flat_powers) 
        max_power = max(flat_powers)  
        mid_power = (min_power + max_power) / 2  # Calculate mid power based on min and max

        power_change = max_power - min_power
        tolerance = 0.1  # Adjust the tolerance relative to the power change

        # Find all voltages corresponding to powers within the tolerance
        min_voltages = [v for v, p in voltage_power_data if abs(p - min_power) < tolerance * power_change]
        max_voltages = [v for v, p in voltage_power_data if abs(p - max_power) < tolerance * power_change]
        mid_voltages = [v for v, p in voltage_power_data if abs(np.mean(p) - mid_power) < tolerance * power_change]

        # Group and average voltages within a 0.2V range
        min_voltages_grouped = self.group_and_average_voltages(min_voltages)
        max_voltages_grouped = self.group_and_average_voltages(max_voltages)

        return min_voltages_grouped, max_voltages_grouped

    def plot_voltage_vs_power(self, voltage_power_data):
        """Plot voltage vs. power and show the plot."""
        voltages, powers = zip(*voltage_power_data)
        flat_powers = powers

        # Create the plot
        plt.figure()
        plt.plot(voltages, flat_powers, marker='o')
        plt.title('Voltage vs Power')
        plt.xlabel('Voltage (V)')
        plt.ylabel('Power (W)')
        plt.grid(True)
        plt.show()

    def group_and_average_voltages(self, voltages, threshold=0.2):
        """Group voltages that are within the given threshold and return their averages."""
        if not voltages:
            return []

        # Sort the voltages first
        voltages = sorted(voltages)

        # Group and average the voltages
        grouped_voltages = []
        current_group = [voltages[0]]

        for v in voltages[1:]:
            if abs(v - current_group[-1]) <= threshold:
                current_group.append(v)
            else:
                # Average the current group and start a new one
                grouped_voltages.append(np.mean(current_group))
                current_group = [v]

        # Append the last group
        grouped_voltages.append(np.mean(current_group))

        return grouped_voltages
    
    def plot_voltage_vs_power(self, voltage_power_data, figSaveName=None):
        import matplotlib.pyplot as plt

        voltages, powers = zip(*voltage_power_data)

        plt.figure()
        plt.plot(voltages, powers, marker='o')
        plt.title('Voltage vs Power')
        plt.xlabel('Voltage (V)')
        plt.ylabel('Power (W)')
        plt.grid(True)

        if figSaveName is not None:
            fig = plt.gcf()
            fig.savefig(figSaveName)
            plt.close(fig)
            print(f"Saved Voltage-Power plot to: {figSaveName}")

 
class GenerateUniqueFilename:
    def __init__(self, basefilename, bases, extension='.ttbin'):
        self.extension = extension  # Set the file extension (e.g., .ttbin)
        
        # Create the data folder and store the path
        self.DataFolder = self.MakeDataFolder()
        
        # Find the highest number across all basis combinations
        highest_number = self.find_highest_number(basefilename, bases)
        
        # Dynamically create the classes and assign basisId and filename with the full path
        self.basis_filenames = {}
        for basis in bases:
            # If no existing number is found, start numbering from 0
            full_filename = os.path.join(self.DataFolder, f'{basefilename}_{basis}_{highest_number}{self.extension}')
            self.basis_filenames[basis] = full_filename

    def MakeDataFolder(self):
        # Get the current directory of the script
        folder = os.path.abspath(os.path.dirname(__file__))

        # Get the current date in YYYYMMDD format
        today_folder = time.strftime('%Y%m%d')

        # Check if the folder for the current date exists, if not, create it
        if os.path.exists(today_folder):
            print("Folder with current date exists")
        else:
            print("Making a folder with the current date")
            os.mkdir(today_folder)

        # Return the full path to the created or existing folder
        return os.path.join(folder, today_folder)

    def find_highest_number(self, basefilename, bases):
        """Find the highest attached number for any of the bases in the folder."""
        # Regular expression to find files with _<number> attached and the .ttbin extension
        number_pattern = re.compile(rf"{basefilename}_(\w+)_(\d+){re.escape(self.extension)}$")

        highest_number = 0  # Start with 0 if no existing files are found

        # List all files in the folder
        existing_files = os.listdir(self.DataFolder)

        # Find the highest number from existing files
        for filename in existing_files:
            match = number_pattern.match(filename)
            if match and match.group(1) in bases:
                # Extract the number and update highest_number
                number = int(match.group(2))
                if number >= highest_number:
                    highest_number = number + 1  # Increment the highest number by 1

        return highest_number

    def get_filenames(self):
        """Return the filenames generated for each basis."""
        return self.basis_filenames
    
    def MakeRunFolder(self):
        """Create a new RunX folder inside the DataFolder, where X is next available run number."""
        base_folder = self.DataFolder

        # Find existing Run folders
        existing_runs = [folder for folder in os.listdir(base_folder) if folder.startswith('Run')]
        run_numbers = [int(folder.replace('Run', '')) for folder in existing_runs if folder.replace('Run', '').isdigit()]
        next_run_number = max(run_numbers, default=0) + 1

        # Create new RunX folder
        run_folder_name = f"Run{next_run_number}"
        run_folder_path = os.path.join(base_folder, run_folder_name)
        os.makedirs(run_folder_path, exist_ok=False)
        print(f"Created new run folder: {run_folder_path}")

        return run_folder_path, next_run_number


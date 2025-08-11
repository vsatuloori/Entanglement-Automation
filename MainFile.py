# Only supports inputs for Interferometer, Optical Switch, Time Tagger and Yokogawa
# Steps to add a new device:
# 1. Create a new class for the device in its own file.
# 2. Import the class in this file.
# 3. Add an elif statement in the create_device function to handle the new device type
# 4. Add a new attribute for the device in the Person class.
# 5. Add the device to the assign_persons_from_config function to create the device and assign it to the person. (Marked with Add here)
import os
import time
import yaml
import math
import datetime
import shutil
from time import sleep
import numpy as np
from Interferometer_v4_20250425 import Interferometer  # Import the Interferometer class
from OpticalSwitch import OSwitch  # Import the OpticalSwitch class
from TimeTaggerFunctions import TimeTagger  # Import TimeTagger
import matplotlib.pyplot as plt

class Person:
    def __init__(self, name, interferometer, optical_switch, time_tagger):
        self.name = name
        self.interferometer = interferometer
        self.optical_switch = optical_switch
        self.time_tagger = time_tagger


def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

#Easily add more devices with the following elif statements

def create_device(device_type, params):
    if device_type == "Interferometer":
        return Interferometer(params)
    elif device_type == "Optical Switch":
        return OSwitch(params)
    elif device_type == "Time Tagger":
        return TimeTagger(params)
    else:
        return None

def assign_persons_from_config(config):
    persons = []
    for person_name, person_data in config.items():
        if not isinstance(person_data, dict):
            continue
        devices = {}
        for device_type, params in person_data.items():
            if device_type in ["Interferometer", "Optical Switch", "Time Tagger"]: # Add here
                devices[device_type] = create_device(device_type, params)
        person = Person(
            name=person_name,
            interferometer=devices.get("Interferometer"),
            optical_switch=devices.get("Optical Switch"),
            time_tagger=devices.get("Time Tagger"),
            #yokogawa = devices.get("Yokogawa")  # Add here if you have a Yokogawa device (example for adding a new device)
        )
        persons.append(person)
    return persons

# Usage
config_path = "/Users/vish/Entanglement Automation/config.yaml" # Adjust the path as needed
config = load_config(config_path)
persons = assign_persons_from_config(config)




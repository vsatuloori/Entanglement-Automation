# Only supports inputs for Interferometer, Optical Switch, Time Tagger and Yokogawa
import os
import time
import yaml
import math
import datetime
import shutil
from time import sleep
import numpy as np
from Interferometer_v5_20250425 import Interferometer  # Import the Interferometer class
from OpticalSwitch import OpticalSwitchDriver  # Import the OpticalSwitch class
from TimeTaggerFunctions import TT  # Import TimeTagger
from PPCL_Bare_Bones import LaserControl
import matplotlib.pyplot as plt

class Person:
    def __init__(self, name, interferometer, optical_switch, time_tagger, laser):
        self.name = name
        self.interferometer = interferometer
        self.optical_switch = optical_switch
        self.time_tagger = time_tagger
        self.laser = laser


def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

#Easily add more devices with the following elif statements

def create_device(device_type, params):
    if device_type == "Interferometer":
        return Interferometer(params)
    elif device_type == "Optical Switch":
        return OpticalSwitchDriver(params)
    elif device_type == "Time Tagger":
        return TT(params)
    elif device_type == "Laser":
        return LaserControl(params)
    else:
        return None  

def assign_persons_from_config(config):
    persons = []
    for person_name, person_data in config.items():
        if not isinstance(person_data, dict):
            continue
        devices = {}
        for device_type, params in person_data.items():
            if device_type in ["Interferometer", "Optical Switch", "Time Tagger", "Laser"]:
                devices[device_type] = create_device(device_type, params)
        person = Person(
            name=person_name,
            interferometer=devices.get("Interferometer"),
            optical_switch=devices.get("Optical Switch"),
            time_tagger=devices.get("Time Tagger"),
            laser=devices.get("Laser"),
        )
        persons.append(person)
    return persons

# Usage
config_path = "config.yaml" # Adjust the path as needed
config = load_config(config_path)
persons = assign_persons_from_config(config)
print(persons[0])



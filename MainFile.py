# Only supports inputs for Interferometer, Optical Switch, Time Tagger and Yokogawa
import os
import time
import yaml
import math
import TimeTagger
import datetime
import shutil
from time import sleep
import numpy as np
from Interferometer_v4_20250425 import Interferometer  # Import the Interferometer class
from OpticalSwitch import OpticalSwitch  # Import the OpticalSwitch class
from TimeTaggerFunctions import TimeTagger  # Import TimeTagger
from yoAQ2212 import Yokogawa  # Import Yokogawa class
from supportingfunctions import GenerateUniqueFilename
import matplotlib.pyplot as plt

class Person:
    def __init__(self, name, interferometer, optical_switch, time_tagger, yokogawa):
        self.name = name
        self.interferometer = interferometer
        self.optical_switch = optical_switch
        self.time_tagger = time_tagger
        self.yokogawa = yokogawa


#Loading neccessary libraries
#!pip install hyperspy
#!pip update h5py
#!pip install exspy
import hyperspy.api as hs
import numpy as np
import matplotlib.pyplot as plt
import h5py
import seaborn as sns
import ipywidgets as widgets
from IPython.display import display
import pandas as pd
import tkinter as tk
from tkinter import messagebox
import exspy

class HDF5SignalProcessor:
    def __init__(self, file_name):
        self.file_name = file_name
        self.signals = []
        self.signal_names = []
        self.process_file()

    def process_file(self):
        with h5py.File(self.file_name, 'r') as f:
            # Process datasets ending with 'SPD'
            f.visititems(self.get_SPD)

            # Process datasets ending with 'MAPIMAGEIPR'
            f.visititems(self.get_MicronsPerPixelX)

            # Process datasets ending with 'SPC'
            f.visititems(self.get_SPC)

    def get_SPD(self, name, obj):
        if isinstance(obj, h5py.Dataset) and name.endswith('SPD'):
            #print(f"Dataset: {name}, shape: {obj.shape}, dtype: {obj.dtype}")

            # Load the data
            data = obj[()]
            data_shape = data.shape

            # data = data.reshape((data_shape[0], data_shape[1], data_shape[2]))

            # Create a HyperSpy Signal1D object just like my previous code
            signal = exspy.signals.EDSSEMSpectrum(data)
            signal.change_dtype('float')
            signal.axes_manager[0].name = 'x'
            signal.axes_manager[0].units = 'um'
            signal.axes_manager[1].name = 'y'
            signal.axes_manager[1].units = 'um'
            signal.axes_manager[2].name = 'Energy'
            signal.axes_manager[2].units = 'keV'
            signal.axes_manager[2].offset = 0
            signal.metadata.General.title = name
            signal.metadata.Signal.signal_type = 'EDS_SEM'
            self.signals.append(signal) # now you can update the signal globally
            self.signal_names.append(name)  # Keep track of signal names

    def get_MicronsPerPixelX(self, name, obj):
        if isinstance(obj, h5py.Dataset) and name.endswith('MAPIMAGEIPR'):
            #print(f"Dataset: {name}, shape: {obj.shape}, dtype: {obj.dtype}")
            #have to consult chatgpt here because the corrupt data structure create many bugs.
            try:
                # Extract 'MicronsPerPixelX' value
                microns_per_pixel_x = obj['MicronsPerPixelX'][()]
                #print('Scale in navigation axis =', microns_per_pixel_x)

                # Find the corresponding signal index
                corresponding_signal_name = name.replace('MAPIMAGEIPR', 'SPD')
                if corresponding_signal_name in self.signal_names:
                    idx = self.signal_names.index(corresponding_signal_name)
                    self.signals[idx].axes_manager[0].scale = microns_per_pixel_x
                    self.signals[idx].axes_manager[1].scale = microns_per_pixel_x
                    #print(f"Set scales for signal {corresponding_signal_name}")
                else:
                    print(f"No corresponding signal found for {name}")
            except Exception as e:
                print(f"Error accessing {name}: {e}") #this is important for debugging, do not delete it

    def get_SPC(self, name, obj):
        if isinstance(obj, h5py.Dataset) and name.endswith('SPC'):
            #print(f"Dataset: {name}, shape: {obj.shape}, dtype: {obj.dtype}")
            try:
                # dispersion
                ev_pch = obj['evPch'][()]
                #print('evPch:', ev_pch)

                # Find the corresponding signal index
                corresponding_signal_name = name.replace('SPC', 'SPD')
                if corresponding_signal_name in self.signal_names:
                    idx = self.signal_names.index(corresponding_signal_name)
                    self.signals[idx].axes_manager[2].scale = ev_pch / 1000  # Convert to kV
                    #print(f"Set energy scale for signal {corresponding_signal_name}")
                else:
                    print(f"No corresponding signal found for {name}")
            except Exception as e:
                print(f"Error accessing {name}: {e}")
    def get_HOSTPARAMS(self, name, obj):
        if isinstance(obj, h5py.Dataset) and name.endswith('HOSTPARAMS'):
            #print(f"Dataset: {name}, shape: {obj.shape}, dtype: {obj.dtype}")
            try:
                # Extract metadata values from HOSTPARAMS
                host_params = obj[0]  # Assuming it's a structured array with one element

                # Find the corresponding signal index
                parent_path = obj.parent.name
                corresponding_signal_name = None
                for signal_name, signal_path in self.signal_paths.items():
                    if signal_path == parent_path:
                        corresponding_signal_name = signal_name
                        break

                if corresponding_signal_name is not None:
                    idx = self.signal_names.index(corresponding_signal_name)
                    signal = self.signals[idx]

                    # Populate metadata from HOSTPARAMS
                    self.populate_metadata_from_HOSTPARAMS(signal, host_params)
                    #print(f"Set metadata for signal {corresponding_signal_name}")
                else:
                    print(f"No corresponding signal found for {name}")
            except Exception as e:
                print(f"Error accessing {name}: {e}")

    def populate_metadata_from_SPC(self, signal, spc_data):
        # Assuming 'spc_data' is an h5py Dataset with structured dtype
        spc = spc_data[0]  # Assuming single-element dataset

        # Populate metadata fields from SPC dataset
        signal.metadata.Acquisition_instrument.SEM.beam_energy = spc['KV']
        signal.metadata.Acquisition_instrument.SEM.Detector.EDS.live_time = spc['LiveTime']
        signal.metadata.Acquisition_instrument.SEM.Detector.EDS.real_time = spc['LiveTime']  # Assuming real_time = live_time
        signal.metadata.Acquisition_instrument.SEM.beam_current = spc['BeamCurrent']
        # Add more fields as necessary based on available data

    def populate_metadata_from_HOSTPARAMS(self, signal, host_params):
        # Populate metadata fields from HOSTPARAMS dataset
        signal.metadata.Acquisition_instrument.SEM.Stage.x = host_params['StageXPosition']
        signal.metadata.Acquisition_instrument.SEM.Stage.y = host_params['StageYPosition']
        signal.metadata.Acquisition_instrument.SEM.Stage.z = host_params['StageZPosition']
        signal.metadata.Acquisition_instrument.SEM.Stage.tilt_alpha = host_params['Tilt']
        signal.metadata.Acquisition_instrument.SEM.Stage.rotation = host_params['Rotation']
        signal.metadata.Acquisition_instrument.SEM.magnification = host_params['Magnification']
        signal.metadata.Acquisition_instrument.SEM.working_distance = host_params['WD']
        signal.metadata.Acquisition_instrument.SEM.beam_current = host_params['BeamCurrent']
        signal.metadata.Acquisition_instrument.SEM.beam_energy = host_params['KV']
        # Add more fields as necessary based on available data

    def get_signals(self):
        return self.signals

    def plot_signals(self):
        for signal in self.signals:
            signal.plot()
"""
example use:
file_name = 'Cu-SS.h5'
processor = HDF5SignalProcessor(file_name)
signals = processor.get_signals()
#processor.plot_signals()
"""

import gradio as gr
from PPCL_Bare_Bones import LaserControl
import numpy as np
from threading import Lock
import glob

class LaserManager:
    def __init__(self):
        self.laser = None
        self.log = []
        self.lock = Lock()
        self.connected = False

    def log_append(self, entry):
        with self.lock:
            self.log.append(entry)
            if len(self.log) > 50:
                self.log.pop(0)

    def list_ports(self):
        return sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))

    def connect(self, port):
        try:
            self.laser = LaserControl(port=port)
            self.laser.connect_laser()
            nop = self.laser.laser.NOP_register()
            self.log_append(f"[CONNECT] NOP: {nop}")
            self.connected = True
            return f"Connected to laser on port {port}. NOP: {nop}"
        except Exception as e:
            return f"Failed to connect: {str(e)}"

    def toggle_laser(self, state):
        if not self.connected:
            return "Laser not connected"
        try:
            if state == "ON":
                self.laser.turn_on()
                self.log_append("[LASER] Turned ON")
                return "Laser turned ON"
            elif state == "OFF":
                self.laser.turn_off()
                self.log_append("[LASER] Turned OFF")
                return "Laser turned OFF"
            else:
                return "Invalid laser state"
        except Exception as e:
            return f"Error toggling laser: {str(e)}"

    def set_wavelength(self, wavelength_nm):
        if not self.connected:
            return "Laser not connected"
        try:
            wl = float(wavelength_nm)
            freq_thz = round(299792458 / (wl * 1e-9) / 1e12, 3)
            self.laser.laser.write_freq(freq_thz)
            confirmed_freq = round(self.laser.laser.read_freq(), 3)
            nop = self.laser.laser.NOP_register()
            success = abs(confirmed_freq - freq_thz) < 0.01
            msg = f"[SET] Wavelength: {wl} nm → Frequency: {freq_thz} THz\nConfirmed Frequency: {confirmed_freq} THz\nNOP: {nop}"
            if not success:
                msg += f"\nWarning: Set and confirmed frequencies differ by more than 10 GHz."
            self.log_append(msg)
            return msg
        except Exception as e:
            return f"Error setting wavelength: {str(e)}"

    def set_power(self, power_input):
        if not self.connected:
            return "Laser not connected"
        try:
            if power_input.lower().endswith("dbm"):
                power_dbm = float(power_input.lower().replace("dbm", "").strip())
                power_mw = 10**(power_dbm / 10)
            else:
                power_mw = float(power_input)
                power_dbm = 10 * np.log10(power_mw)

            response = self.laser.laser.write_power(power_mw * 100)  # convert to internal scale
            nop = self.laser.laser.NOP_register()
            msg = f"[SET] Power: {power_mw:.2f} mW ({power_dbm:.2f} dBm)\nResponse: {response}\nNOP: {nop}"
            self.log_append(msg)
            return msg
        except Exception as e:
            return f"Error setting power: {str(e)}"

    def disconnect(self):
        if not self.connected:
            return "Laser already disconnected"
        try:
            self.laser.disconnect()
            self.connected = False
            self.log_append("[DISCONNECT] Laser disconnected")
            return "Laser disconnected"
        except Exception as e:
            return f"Error disconnecting: {str(e)}"

    def get_logs(self):
        return "\n".join(self.log)

laser_mgr = LaserManager()

def refresh_ports():
    return gr.update(choices=laser_mgr.list_ports())

def connect_fn(port):
    return laser_mgr.connect(port)

def toggle_laser_fn(state):
    return laser_mgr.toggle_laser(state)

def set_wavelength_fn(wavelength):
    return laser_mgr.set_wavelength(wavelength)

def set_power_fn(power):
    return laser_mgr.set_power(power)

def disconnect_fn():
    return laser_mgr.disconnect()

def get_log_fn():
    return laser_mgr.get_logs()

with gr.Blocks(title="INQNET-PPCL laser control") as demo:
    gr.Markdown("# INQNET-PPCL Laser Control")

    with gr.Row():
        port_dropdown = gr.Dropdown(label="Available Ports", choices=laser_mgr.list_ports())
        refresh_btn = gr.Button("Refresh Ports")
        connect_btn = gr.Button("Connect")

    with gr.Row():
        laser_radio = gr.Radio(choices=["ON", "OFF"], label="Laser Control")
        wavelength_input = gr.Textbox(label="Set Wavelength (nm)", value="1550")
        set_wl_btn = gr.Button("Set Wavelength")

    with gr.Row():
        power_input = gr.Textbox(label="Set Power (mW or dBm)", value="6")
        set_power_btn = gr.Button("Set Power")

    disconnect_btn = gr.Button("Disconnect")
    log_output = gr.Textbox(label="Laser Log", lines=15, interactive=False)
    log_refresh_btn = gr.Button("Refresh Log")

    refresh_btn.click(fn=refresh_ports, outputs=port_dropdown)
    connect_btn.click(fn=connect_fn, inputs=port_dropdown, outputs=log_output)
    laser_radio.change(fn=toggle_laser_fn, inputs=laser_radio, outputs=log_output)
    set_wl_btn.click(fn=set_wavelength_fn, inputs=wavelength_input, outputs=log_output)
    set_power_btn.click(fn=set_power_fn, inputs=power_input, outputs=log_output)
    disconnect_btn.click(fn=disconnect_fn, outputs=log_output)
    log_refresh_btn.click(fn=lambda: laser_mgr.get_logs(), outputs=log_output)

if __name__ == '__main__':
    # demo.launch()

    demo.launch(server_port=7860, server_name="0.0.0.0", inbrowser=True)


import gradio as gr
import serial.tools.list_ports
from EDFAControl import EDFAControl

edfa = None
log_output = ""

def list_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

def connect_to_edfa(port, baud_rate):
    global edfa
    try:
        edfa = EDFAControl(port=port, baud_rate=int(baud_rate))
        edfa.connect()
        return f"✅ Connected to {port} @ {baud_rate} baud."
    except Exception as e:
        return f"❌ Connection failed: {str(e)}"

def handle_pump_toggle(state):
    if edfa is None:
        return "❌ EDFA not connected."
    try:
        if state == "ON":
            return edfa.pump_on()
        else:
            return edfa.pump_off()
    except Exception as e:
        return f"⚠️ Pump toggle error: {e}"

def apply_current(current, step_size):
    if edfa is None:
        return "❌ EDFA not connected."
    try:
        edfa.step_size = int(step_size)
        return edfa.set_current(current)
    except Exception as e:
        return f"⚠️ Failed to set current: {e}"

def get_current():
    if edfa is None:
        return "❌ EDFA not connected."
    try:
        curr = edfa.get_current()
        return f"📈 Current pump value: {curr} mA"
    except Exception as e:
        return f"⚠️ Failed to get current: {e}"

with gr.Blocks(title="INQNET-EDFA") as demo:
    gr.Markdown("## 💡 INQNET-EDFA Controller")

    with gr.Row():
        port_dropdown = gr.Dropdown(choices=list_ports(), label="USB Port")
        refresh_btn = gr.Button("🔄 Refresh Ports")

    with gr.Row():
        baud_input = gr.Number(value=9600, label="Baud Rate")
        connect_btn = gr.Button("🔌 Connect")

    with gr.Row():
        pump_toggle = gr.Radio(["OFF", "ON"], label="Pump Power", value="OFF")

    with gr.Row():
        current_slider = gr.Slider(0, 890, value=0, step=5, label="Set Current (mA)")
        current_input = gr.Number(value=0, label="or Type Current")
        step_input = gr.Number(value=10, label="Step Size (mA)")
        apply_btn = gr.Button("✅ Apply Current")
        get_btn = gr.Button("📤 Get Current")

    output_log = gr.Textbox(label="Log Output", lines=10)

    # Bind actions
    refresh_btn.click(fn=list_ports, outputs=port_dropdown)
    connect_btn.click(fn=connect_to_edfa, inputs=[port_dropdown, baud_input], outputs=output_log)
    pump_toggle.change(fn=handle_pump_toggle, inputs=pump_toggle, outputs=output_log)
    apply_btn.click(fn=apply_current, inputs=[current_input, step_input], outputs=output_log)
    get_btn.click(fn=get_current, outputs=output_log)

    # Sync slider <-> input box
    current_slider.change(fn=lambda x: x, inputs=current_slider, outputs=current_input)
    current_input.change(fn=lambda x: x, inputs=current_input, outputs=current_slider)

if __name__ == "__main__":
    demo.launch()

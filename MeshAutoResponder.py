import tkinter as tk
from tkinter import simpledialog, messagebox
import meshtastic.serial_interface
from pubsub import pub
from datetime import datetime

class InputDialog:
    def __init__(self, root, initial_reply_message="", initial_signal=""):
        self.top = tk.Toplevel(root)
        self.top.geometry("750x350")
        self.top.title("Input Settings")

        frame = tk.Frame(self.top)
        frame.pack(pady=10)

        tk.Label(frame, text="Enter the reply message (max 120 chars):").pack(anchor='w')

        text_frame = tk.Frame(frame)
        text_frame.pack(fill='both', expand=True)

        self.reply_message_text = tk.Text(text_frame, width=60, height=4, wrap=tk.WORD)
        self.reply_message_text.insert(tk.END, initial_reply_message)
        self.reply_message_text.pack(side=tk.LEFT, padx=(0, 10))

        # Character count label placed right next to the text box
        self.char_count_label = tk.Label(text_frame, text=f"0/120")
        self.char_count_label.pack(side=tk.LEFT, fill=tk.Y)
        self.reply_message_text.bind("<KeyRelease>", self.update_char_count)

        signal_frame = tk.Frame(self.top)
        signal_frame.pack(fill='both', expand=True)

        tk.Label(signal_frame, text="Enter the signal variable:").pack(anchor='w')
        self.signal_entry = tk.Entry(signal_frame, width=50)
        self.signal_entry.insert(0, initial_signal)
        self.signal_entry.pack()

        self.submit_button = tk.Button(self.top, text="Submit", command=self.on_submit)
        self.submit_button.pack(pady=20)

        self.reply_message = None
        self.signal = None

    def on_submit(self):
        reply_message = self.reply_message_text.get("1.0", "end-1c").strip()
        signal = self.signal_entry.get()

        if len(reply_message) > 120:
            messagebox.showerror("Error", "The reply message must be less than or equal to 120 characters.")
        else:
            self.reply_message = reply_message
            self.signal = signal
            self.top.destroy()

    def update_char_count(self, event=None):
        # Update the character count based on the text area content
        char_count = len(self.reply_message_text.get("1.0", "end-1c"))
        self.char_count_label.config(text=f"{char_count}/120")

# Read settings from file
def read_settings():
    try:
        with open("settings.txt", "r") as file:
            lines = file.readlines()
            settings = {}
            for line in lines:
                key, value = line.strip().split("=")
                settings[key] = value
        return settings["reply_message"], settings["signal"]
    except FileNotFoundError:
        return "", ""

# Function to initialize the GUI for input
def init_gui(root):
    initial_reply_message, initial_signal = read_settings()
    input_dialog = InputDialog(root, initial_reply_message, initial_signal)
    root.wait_window(input_dialog.top)
    return input_dialog.reply_message, input_dialog.signal

# Main GUI application
def run_gui():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    reply_message, signal = init_gui(root)

    if not reply_message or not signal:
        print("No input provided. Exiting.")
        return

    # Save to a settings file
    with open("settings.txt", "w") as file:
        file.write(f"reply_message={reply_message}\n")
        file.write(f"signal={signal}\n")

    interface = meshtastic.serial_interface.SerialInterface()

    def onReceive(packet, interface):
        try:
            if 'decoded' in packet and packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP':
                message_bytes = packet['decoded']['payload']
                message_string = message_bytes.decode('utf-8')
                print(f"Received: {message_string}")
                if signal in message_string:
                    date_prefix = datetime.now().strftime("%m-%d-%Y")
                    send_message(f"{date_prefix} {reply_message}")
        except KeyError as e:
            print(f"Error processing packet: {e}")

    pub.subscribe(onReceive, 'meshtastic.receive')

    def send_message(message):
        interface.sendText(message)
        print(f"Sent: {message}")

    root.mainloop()

if __name__ == "__main__":
    run_gui()


import requests
import json
import logging
from tkinter import *
from tkinter import messagebox
import tkinter.scrolledtext as scrolledtext


class TailscaleAPI:
    def __init__(self):
        self.api_key = None
        self.tailnet = None
        self.devices = []

    def login(self, api_key, tailnet):
        self.api_key = api_key
        self.tailnet = tailnet
        response = requests.get(
            f"https://api.tailscale.com/api/v2/tailnet/{self.tailnet}/devices",
            auth=(self.api_key, "")
        )
        data = response.json()
        self.devices = data.get("devices", [])
        return data

    def apply_tags(self, device_id, tags):
        headers = {
            'Content-Type': 'application/json',
        }
        data = json.dumps({
            'tags': tags
        })
        response = requests.post(
            f"https://api.tailscale.com/api/v2/device/{device_id}/tags",
            headers=headers,
            data=data,
            auth=(self.api_key, "")
        )
        return response




class GUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Tailscale Manager")

        # Create main container frame
        self.container = Frame(self.master)
        self.container.pack(fill=BOTH, expand=True)

        # Create API Key, Tailnet Name, and Login frame
        self.login_frame = self.create_frame(self.container, X, 10, (10, 0))
        self.api_key_entry = self.create_entry(self.login_frame, "Enter API Key", LEFT, X, 0, 0, True)
        self.tailnet_entry = self.create_entry(self.login_frame, "Enter Tailnet Name", LEFT, X, (10, 0), 0, True)
        self.login_button = Button(self.login_frame, text="Login")
        self.login_button.pack(side=LEFT, padx=(10, 0), pady=0)

        # Create Search Devices and Device List frame
        self.device_frame = self.create_frame(self.container, BOTH, 10, (5, 0), True)
        self.search_entry = self.create_entry(self.device_frame, "Search devices", None, X, 0, 0)
        self.device_list_frame = self.create_frame(self.device_frame, BOTH, 0, 0, True)

        self.device_list_scrollbar = Scrollbar(self.device_list_frame)
        self.device_list_scrollbar.pack(side=RIGHT, fill=Y)

        self.device_list = Listbox(self.device_list_frame, selectmode=MULTIPLE, yscrollcommand=self.device_list_scrollbar.set)
        self.device_list.pack(fill=BOTH, expand=True)
        self.device_list_scrollbar.config(command=self.device_list.yview)

        self.device_list.bind('<<ListboxSelect>>', self.on_select)
        self.selected_devices = set()  # Store the current selection here.

        # Create Tag Entry, Apply Tags, and Show Logs frame
        self.tag_frame = self.create_frame(self.container, X, 10, (5, 0))
        self.tag_entry = self.create_entry(self.tag_frame, "work-device, test-devices, blah-tag", LEFT, X, 0, 0, True)
        self.apply_tags_button = Button(self.tag_frame, text="Apply Tags")
        self.apply_tags_button.pack(side=LEFT, padx=(10, 0), pady=0)

        # Create Show Logs frame
        self.show_logs_frame = self.create_frame(self.container, X, 10, 10)
        self.show_logs_button = Button(self.show_logs_frame, text="Show Logs")
        self.show_logs_button.pack(side=RIGHT, padx=0, pady=0, expand=True, fill=X)

        # Create Console Logs frame
        self.console_frame = self.create_frame(self.container, None, 0, 0)
        self.console_text = scrolledtext.ScrolledText(self.console_frame, height=10)
        self.console_text.pack(fill=BOTH, expand=True)

        # Hide the console logs frame initially
        self.console_frame.pack_forget()

    def create_frame(self, master, fill=None, padx=0, pady=0, expand=False):
        frame = Frame(master)
        frame.pack(fill=fill, padx=padx, pady=pady, expand=expand)
        return frame

    def create_entry(self, master, default_text, side=None, fill=None, padx=0, pady=0, expand=False):
        entry = Entry(master)
        entry.insert(0, default_text)
        entry.pack(side=side, fill=fill, padx=padx, pady=pady, expand=expand)
        return entry

    def on_select(self, event):
        current_selection = set(self.device_list.curselection())
        added = current_selection - self.selected_devices
        removed = self.selected_devices - current_selection
        self.selected_devices = current_selection
        for index in added:
            print(f"{self.device_list.get(index)} device selected")
        for index in removed:
            print(f"{self.device_list.get(index)} device deselected")



class TailscaleManager:
    def __init__(self, master):
        self.api = TailscaleAPI()
        self.gui = GUI(master)

        self.gui.login_button.configure(command=self.login)
        self.gui.search_entry.bind('<KeyRelease>', self.update_device_list)
        self.gui.apply_tags_button.configure(command=self.apply_tags)
        self.gui.show_logs_button.configure(command=self.toggle_logs)
        self.gui.device_list.bind('<<ListboxSelect>>', self.on_device_select)

        self.logger = logging.getLogger("console_logger")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.CustomHandler(self.gui.console_text))

        self.master = master
        self.master.grid_rowconfigure(0, weight=0)
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_rowconfigure(2, weight=0)
        self.master.grid_rowconfigure(3, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

    def login(self):
        data = self.api.login(self.gui.api_key_entry.get(), self.gui.tailnet_entry.get())
        self.log_message("API Response:")
        self.log_message(json.dumps(data, indent=4))
        self.update_device_list()

    def update_device_list(self, event=None):
        search_term = self.gui.search_entry.get().lower()
        self.gui.device_list.delete(0, END)
        for device in self.api.devices:
            if search_term in device["name"].lower() or search_term == "search devices":
                self.gui.device_list.insert(END, device["name"])

    def on_device_select(self, event):
        selected_indices = self.gui.device_list.curselection()
        self.log_message(f"Adding {len(selected_indices)} device(s) into list")

    def apply_tags(self):
        selected_devices = [self.api.devices[i] for i in self.gui.device_list.curselection()]
        selected_tags = ['tag:'+tag.strip() for tag in self.gui.tag_entry.get().split(",")]
        for device in selected_devices:
            device_id = device["nodeId"]
            response = self.api.apply_tags(device_id, selected_tags)
            if response.status_code == 200:
                self.log_message(f"Tags updated for device {device['name']}")
            else:
                error_message = f"Failed to update tags for device {device['name']}. Status code: {response.status_code}, Response: {response.json()}"
                self.log_message(error_message)
                messagebox.showerror("Error", error_message)
                
        # Prompt to show which tags will be applied to which devices.
        tag_text = ', '.join(selected_tags)
        device_text = ', '.join(device['name'] for device in selected_devices)
        prompt_text = f"The tags {tag_text} will be applied to the following devices: {device_text}. Press OK to continue."
        prompt_result = messagebox.askokcancel("Confirmation", prompt_text)
        if prompt_result:
            self.log_message("Applying tags...")
        else:
            self.log_message("Tag application cancelled.")


    def toggle_logs(self):
        if self.gui.console_frame.winfo_ismapped():
            self.gui.console_frame.pack_forget()
            self.gui.show_logs_button.configure(text="Show Logs")
        else:
            self.gui.console_frame.pack(fill=BOTH, padx=10, pady=10, expand=True)
            self.gui.show_logs_button.configure(text="Hide Logs")

    def log_message(self, message):
        self.logger.info(message)

    class CustomHandler(logging.Handler):
        def __init__(self, text_widget):
            logging.Handler.__init__(self)
            self.text_widget = text_widget

        def emit(self, record):
            log_message = self.format(record)
            self.text_widget.insert(END, log_message + "\n")
            self.text_widget.see(END)

def main():
    root = Tk()
    app = TailscaleManager(root)
    root.geometry("800x500")  # Set the initial size of the window
    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(3, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.mainloop()

if __name__ == '__main__':
    main()
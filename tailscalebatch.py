import requests
import json
import logging
from tkinter import *
from tkinter import messagebox
import tkinter.scrolledtext as scrolledtext
import time

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
        if response.status_code == 200:
            data = response.json()
            self.devices = data.get("devices", [])
        return response

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

        # Create Device frame to group search devices, buttons, and device lists
        self.device_frame = self.create_frame(self.container, BOTH, 10, (5, 0), True)

        # Create a new frame for grouping search, select all and add to target buttons
        self.device_actions_frame = self.create_frame(self.device_frame, X, 0, 0, False)
        self.search_entry = self.create_entry(self.device_actions_frame, "Search devices", LEFT, X, 0, 0)
        self.select_all_visible_button = Button(self.device_actions_frame, text="Select All Visible Devices")
        self.select_all_visible_button.pack(side=LEFT, padx=(10, 0), pady=0)
        self.add_to_target_button = Button(self.device_actions_frame, text="Add Selection to Target")
        self.add_to_target_button.pack(side=LEFT, padx=(10, 0), pady=0)
        self.select_all_visible_button.configure(command=self.select_all_visible_devices)

        # Create two separate device lists frame: available and target
        self.device_lists_frame = self.create_frame(self.device_frame, BOTH, 0, 0, True)
        self.available_device_list_frame = self.create_frame(self.device_lists_frame, BOTH, 0, 0, True)
        self.target_device_list_frame = self.create_frame(self.device_lists_frame, BOTH, 0, 0, True)

        # Create two separate device lists: available and target
        self.available_device_list = self.create_device_list(self.available_device_list_frame)
        self.target_device_list = self.create_device_list(self.target_device_list_frame, selectmode='DISABLED')
        self.target_device_list.bind('<<ListboxSelect>>', lambda event: self.target_device_list.selection_clear(0, END))

        # Create Tag Entry, Apply Tags, and Show Logs frame
        self.tag_frame = self.create_frame(self.container, X, 10, (5, 0))
        self.tag_entry = self.create_entry(self.tag_frame, "work-device, test-devices, blah-tag", LEFT, X, 0, 0, True)
        self.clear_target_list_button = Button(self.tag_frame, text="Clear Target List")
        self.clear_target_list_button.pack(side=LEFT, padx=(10, 0), pady=0)
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

    # Prevent selection/deselection when clicking on whitespace.
    def on_mouse_click(self, event):
        index = self.device_list.nearest(event.y)
        if "empty" in self.device_list.itemcget(index, "style"):
            # Ignore clicks on empty items
            return "break"

    def create_device_list(self, master, selectmode='EXTENDED'):
        scrollbar = Scrollbar(master)
        scrollbar.pack(side=RIGHT, fill=Y)

        listbox = Listbox(master, selectmode=MULTIPLE, yscrollcommand=scrollbar.set)
        listbox.pack(fill=BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        return listbox

    def select_all_visible_devices(self):
        self.available_device_list.select_set(0, END)



class TailscaleManager:
    SUCCESS = 25
    LOG_COLORS = {
        logging.INFO: "gray30",
        logging.ERROR: "red",
        logging.WARNING: "orange",
        logging.DEBUG: "black",
        logging.CRITICAL: "red",
        SUCCESS: "green",
    }

    LOG_PREFIXES = {
        logging.INFO: "[INFO] ",
        logging.ERROR: "[ERROR] ",
        logging.WARNING: "[WARNING] ",
        logging.DEBUG: "[DEBUG] ",
        logging.CRITICAL: "[CRITICAL] ",
        SUCCESS: "[SUCCESS] ",
    }

    def __init__(self, master):
        self.api = TailscaleAPI()
        self.gui = GUI(master)

        self.gui.login_button.configure(command=self.login)
        self.gui.search_entry.bind('<KeyRelease>', self.update_device_list)
        self.gui.clear_target_list_button.configure(command=self.clear_target_list)
        self.gui.apply_tags_button.configure(command=self.apply_tags)
        self.gui.show_logs_button.configure(command=self.toggle_logs)
        self.gui.available_device_list.bind('<<ListboxSelect>>', self.on_device_select)
        self.gui.select_all_visible_button.configure(command=self.select_all_visible)
        self.gui.add_to_target_button.configure(command=self.add_to_target)
        self.gui.search_entry.config(state=DISABLED)
        self.gui.select_all_visible_button.config(state=DISABLED)
        self.gui.add_to_target_button.config(state=DISABLED)
        self.gui.clear_target_list_button.config(state=DISABLED)
        self.gui.apply_tags_button.config(state=DISABLED)

        self.logger = logging.getLogger("console_logger")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.CustomHandler(self.gui.console_text))
        formatter = logging.Formatter('%(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        self.logger.handlers[0].setFormatter(formatter)

        self.master = master
        self.master.grid_rowconfigure(0, weight=0)
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_rowconfigure(2, weight=0)
        self.master.grid_rowconfigure(3, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

    def login(self):
        response = self.api.login(self.gui.api_key_entry.get(), self.gui.tailnet_entry.get())
        if response.status_code == 200:
            data = response.json()
            num_devices = len(data.get('devices', []))
            self.log_message("Login successful", level=self.SUCCESS)
            self.log_message(f"Added {num_devices} device(s) to list", level=logging.INFO)
            self.update_device_list()
            self.gui.search_entry.config(state=NORMAL)
            self.gui.select_all_visible_button.config(state=NORMAL)
            self.gui.add_to_target_button.config(state=NORMAL)
            self.gui.clear_target_list_button.config(state=NORMAL)
            self.gui.apply_tags_button.config(state=NORMAL)

        else:
            self.log_message("API Response:\n" + json.dumps(response.json(), indent=4), level=logging.ERROR)


    def update_device_list(self, event=None):
        search_term = self.gui.search_entry.get().lower()
        self.gui.available_device_list.delete(0, END)
        if search_term != "search devices":
            self.log_message("Search performed, clearing current selection", level=logging.INFO)
        for device in self.api.devices:
            if search_term in device["name"].lower() or search_term == "search devices":
                self.gui.available_device_list.insert(END, device["name"])

    def on_device_select(self, event):
        selected_indices = self.gui.available_device_list.curselection()
        if len(selected_indices) > 0:
            self.log_message(f"Selected {len(selected_indices)} device(s) from available list", level=logging.INFO, ignore_duplicates=True)
        else:
            self.log_message("No devices selected in device list", level=logging.WARNING, ignore_duplicates=True)

    def on_target_device_select(self, event):
        # Handle the event for selecting device from target_device_list
        selected_indices = self.gui.target_device_list.curselection()
        self.log_message(f"Selected {len(selected_indices)} device(s) from target list", level=logging.INFO)

    def select_all_visible(self):
        self.gui.available_device_list.select_set(0, END)
        selected_indices = self.gui.available_device_list.curselection()
        self.log_message(f"All visible {len(selected_indices)} devices have been selected.", level=logging.INFO)


    def add_to_target(self):
        selected_indices = self.gui.available_device_list.curselection()
        selected_devices = [self.gui.available_device_list.get(i) for i in selected_indices]

        # Add selected devices to target list
        for device in selected_devices:
            self.gui.target_device_list.insert(END, device)

        # Remove selected devices from available list
        for index in reversed(selected_indices):  # reversed to avoid skipping items
            self.gui.available_device_list.delete(index)

        self.log_message(f"Moved {len(selected_devices)} device(s) to target list", level=logging.INFO)

    def clear_target_list(self):
        self.gui.target_device_list.delete(0, END)
        self.update_device_list()  # Refresh the available devices based on the current search term
        self.log_message("Cleared all devices from target list", level=logging.INFO, ignore_duplicates=True)



    def apply_tags(self):
        selected_devices = [self.api.devices[i] for i in self.gui.target_device_list.curselection()]
        selected_tags = ['tag:'+tag.strip() for tag in self.gui.tag_entry.get().split(",")]
        # Prompt to show which tags will be applied to which devices.
        tag_text = ', '.join(selected_tags)
        device_text = ', '.join(device['name'] for device in selected_devices)
        prompt_text = f"The tags {tag_text} will be applied to the following devices: {device_text}. Press OK to continue."
        prompt_result = messagebox.askokcancel("Confirmation", prompt_text)
        if prompt_result:
            self.log_message("Applying tags...", level=logging.INFO)
            for device in selected_devices:
                device_id = device["nodeId"]
                response = self.api.apply_tags(device_id, selected_tags)
                if response.status_code == 200:
                    self.log_message(f"Tags updated for device {device['name']}", level=self.SUCCESS)
                else:
                    error_message = f"Failed to update tags for device {device['name']}. Status code: {response.status_code}, Response: {response.json()}"
                    self.log_message(error_message, level=logging.ERROR)
                    messagebox.showerror("Error", error_message)
        else:
            self.log_message("Tag application cancelled.", level=logging.CRITICAL)
        self.clear_target_list()  # Clear target list after applying tags


    def toggle_logs(self):
        if self.gui.console_frame.winfo_ismapped():
            self.gui.console_frame.pack_forget()
            self.gui.show_logs_button.configure(text="Show Logs")
        else:
            self.gui.console_frame.pack(fill=BOTH, padx=10, pady=10, expand=True)
            self.gui.show_logs_button.configure(text="Hide Logs")

    def log_message(self, message, level=logging.INFO, ignore_duplicates=False):
        last_log_message = self.gui.console_text.get("end-2c linestart", "end-1c")
        if not ignore_duplicates or last_log_message != message:
            if level == logging.INFO:
                self.logger.info(message)
            elif level == logging.WARNING:
                self.logger.warning(message)
            elif level == logging.ERROR:
                self.logger.error(message)
            elif level == logging.DEBUG:
                self.logger.debug(message)
            elif level == logging.CRITICAL:
                self.logger.critical(message)


    class CustomHandler(logging.Handler):
        def __init__(self, text_widget):
            logging.Handler.__init__(self)
            self.text_widget = text_widget

        def emit(self, record):
            log_message = self.format(record)  # This now includes the timestamp
            fg = TailscaleManager.LOG_COLORS.get(record.levelno, "black")
            prefix = TailscaleManager.LOG_PREFIXES.get(record.levelno, "")

            # Create a unique tag using the current timestamp
            tag = str(time.time())
            self.text_widget.tag_config(tag, foreground=fg)

            self.text_widget.insert(END, prefix + log_message + "\n", tag)
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
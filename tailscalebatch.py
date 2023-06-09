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

        # Create Device frame to group search devices, buttons, and device lists
        self.device_frame = self.create_frame(self.container, BOTH, 10, (5, 0), True)

        # Create a new frame for grouping search, select all and add to target buttons
        self.device_actions_frame = self.create_frame(self.device_frame, X, 0, 0, False)
        self.search_entry = self.create_entry(self.device_actions_frame, "Search devices", LEFT, X, 0, 0)
        self.select_all_visible_button = Button(self.device_actions_frame, text="Select All Visible Devices")
        self.select_all_visible_button.pack(side=LEFT, padx=(10, 0), pady=0)
        self.add_to_target_button = Button(self.device_actions_frame, text="Add Selected to Target")
        self.add_to_target_button.pack(side=LEFT, padx=(10, 0), pady=0)
        self.select_all_visible_button.configure(command=self.select_all_visible_devices)

        # Create two separate device lists frame: available and target
        self.device_lists_frame = self.create_frame(self.device_frame, BOTH, 0, 0, True)
        self.available_device_list_frame = self.create_frame(self.device_lists_frame, BOTH, 0, 0, True)
        self.target_device_list_frame = self.create_frame(self.device_lists_frame, BOTH, 0, 0, True)

        # Create two separate device lists: available and target
        self.available_device_list = self.create_device_list(self.available_device_list_frame)
        self.target_device_list = self.create_device_list(self.target_device_list_frame)

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

    # Prevent selection/deselection when clicking on whitespace.
    def on_mouse_click(self, event):
        index = self.device_list.nearest(event.y)
        if "empty" in self.device_list.itemcget(index, "style"):
            # Ignore clicks on empty items
            return "break"

    def create_device_list(self, master):
        scrollbar = Scrollbar(master)
        scrollbar.pack(side=RIGHT, fill=Y)

        listbox = Listbox(master, selectmode=MULTIPLE, yscrollcommand=scrollbar.set)
        listbox.pack(fill=BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        return listbox

    def select_all_visible_devices(self):
        self.available_device_list.select_set(0, END)



class TailscaleManager:
    def __init__(self, master):
        self.api = TailscaleAPI()
        self.gui = GUI(master)

        self.gui.login_button.configure(command=self.login)
        self.gui.search_entry.bind('<KeyRelease>', self.update_device_list)
        self.gui.apply_tags_button.configure(command=self.apply_tags)
        self.gui.show_logs_button.configure(command=self.toggle_logs)
        self.gui.available_device_list.bind('<<ListboxSelect>>', self.on_device_select)
        self.gui.target_device_list.bind('<<ListboxSelect>>', self.on_device_select)
        self.gui.select_all_visible_button.configure(command=self.select_all_visible)
        self.gui.add_to_target_button.configure(command=self.add_to_target)

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
        response = self.api.login(self.gui.api_key_entry.get(), self.gui.tailnet_entry.get())
        if response.status_code == 200:
            data = response.json()
            num_devices = len(data.get('devices', []))
            self.log_message(f"Added {num_devices} device(s) to list")
            self.update_device_list()
        else:
            self.log_message("API Response:")
            self.log_message(json.dumps(response.json(), indent=4))

    def update_device_list(self, event=None):
        search_term = self.gui.search_entry.get().lower()
        self.gui.device_list.delete(0, END)
        if search_term != "search devices":
            self.log_message("Search performed, clearing current selection")
        for device in self.api.devices:
            if search_term in device["name"].lower() or search_term == "search devices":
                self.gui.device_list.insert(END, device["name"])

    def on_device_select(self, event):
        # Handle the event for selecting device from available_device_list and target_device_list
        selected_indices = event.gui.available_device_list.curselection()
        self.log_message(f"Selected {len(selected_indices)} device(s) from available list")

    def on_target_device_select(self, event):
        # Handle the event for selecting device from target_device_list
        selected_indices = self.gui.target_device_list.curselection()
        self.log_message(f"Selected {len(selected_indices)} device(s) from target list")

    def select_all_visible(self):
        self.gui.available_device_list.select_set(0, END)
        self.log_message("All visible devices have been selected.")

    def add_to_target(self):
        selected_indices = self.gui.available_device_list.curselection()
        for index in selected_indices:
            self.gui.target_device_list.insert(END, self.gui.available_device_list.get(index))
        self.log_message(f"Moved {len(selected_indices)} device(s) to target list")



    def apply_tags(self):
        selected_devices = [self.api.devices[i] for i in self.gui.target_device_list.curselection()]
        selected_tags = ['tag:'+tag.strip() for tag in self.gui.tag_entry.get().split(",")]
        # Prompt to show which tags will be applied to which devices.
        tag_text = ', '.join(selected_tags)
        device_text = ', '.join(device['name'] for device in selected_devices)
        prompt_text = f"The tags {tag_text} will be applied to the following devices: {device_text}. Press OK to continue."
        prompt_result = messagebox.askokcancel("Confirmation", prompt_text)
        if prompt_result:
            self.log_message("Applying tags...")
            for device in selected_devices:
                device_id = device["nodeId"]
                response = self.api.apply_tags(device_id, selected_tags)
                if response.status_code == 200:
                    self.log_message(f"Tags updated for device {device['name']}")
                else:
                    error_message = f"Failed to update tags for device {device['name']}. Status code: {response.status_code}, Response: {response.json()}"
                    self.log_message(error_message)
                    messagebox.showerror("Error", error_message)
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
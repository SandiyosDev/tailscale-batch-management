import requests
import json
from tkinter import *
from tkinter import messagebox

class TailscaleManager:
    def __init__(self, master):
        self.master = master
        self.master.title("Tailscale Manager")
        self.api_key = None
        self.tailnet = None
        self.devices = []
        self.tags = []

        # Create widgets
        self.api_key_entry = Entry(self.master)
        self.api_key_entry.insert(0, "Enter API Key")  # Placeholder text for API Key
        self.api_key_entry.pack(fill=X, padx=10, pady=(10, 0))

        self.tailnet_entry = Entry(self.master)
        self.tailnet_entry.insert(0, "Enter Tailnet Name")  # Placeholder text for Tailnet Name
        self.tailnet_entry.pack(fill=X, padx=10, pady=(5, 0))

        self.login_button = Button(self.master, text="Login", command=self.login)
        self.login_button.pack(pady=(5, 0))

        self.search_entry = Entry(self.master)
        self.search_entry.insert(0, "Search devices")  # Placeholder text for search
        self.search_entry.pack(fill=X, padx=10, pady=(5, 0))
        self.search_entry.bind('<KeyRelease>', self.update_device_list)

        self.device_list = Listbox(self.master, selectmode=MULTIPLE)
        self.device_list.pack(fill=BOTH, expand=True, padx=10, pady=(5, 0))

        self.select_all_button = Button(self.master, text="Select All Visible Devices", command=self.select_all)
        self.select_all_button.pack(pady=(5, 0))

        self.tag_entry = Entry(self.master)
        self.tag_entry.insert(0, "Enter tags (comma-separated)")  # Placeholder text for tags
        self.tag_entry.pack(fill=X, padx=10, pady=(5, 0))

        self.apply_tags_button = Button(self.master, text="Apply Tags", command=self.apply_tags)
        self.apply_tags_button.pack(pady=(5, 10))

    def login(self):
        self.api_key = self.api_key_entry.get()
        self.tailnet = self.tailnet_entry.get()
        self.update_device_list()

    def update_device_list(self, event=None):
        # Fetch the list of devices using the API key and tailnet name
        response = requests.get(
            f"https://api.tailscale.com/api/v2/tailnet/{self.tailnet}/devices",
            auth=(self.api_key, "")
        )
        data = response.json()
        self.devices = data["devices"] if "devices" in data else []  # Extract the "devices" list
        print(self.devices)  # Added this line to print the devicws
        search_term = self.search_entry.get().lower()
        self.device_list.delete(0, END)
        for device in self.devices:
            print(device)  # Add this line to print the device
            if search_term in device["hostname"].lower():
                self.device_list.insert(END, device["hostname"])

    def select_all(self):
        # Select all visible devices
        self.device_list.select_set(0, END)

    def apply_tags(self):
        # Apply the selected tags to the selected devices
        selected_devices = [self.devices[i] for i in self.device_list.curselection()]
        selected_tags = self.tag_entry.get().split(",")  # Split tags by comma
        for device in selected_devices:
            device_id = device["nodeId"]
            response = requests.post(
                f"https://api.tailscale.com/api/v2/device/{device_id}/tags",
                json={"tags": selected_tags},
                auth=(self.api_key, "")
            )
            if response.status_code != 200:
                messagebox.showerror("Error", f"Failed to update tags for device {device['hostname']}")

root = Tk()
app = TailscaleManager(root)
root.geometry("400x300")  # Set the initial size of the window
root.mainloop()
# THIS SCRIPT IS WORK-IN-PROGRESS
# Tailscale Manager

This is a Python script that provides a simple GUI interface for managing Tailscale devices using the Tailscale API. It allows you to log in with your API key, fetch the list of devices associated with a specific tailnet, search for devices, select multiple devices, and apply tags to the selected devices.

## Prerequisites

Before running this script, make sure you have the following:

- Python 3.x installed on your system.
- The `requests` library installed. You can install it by running `pip install requests`.
- The `tkinter` library installed. It is usually included with Python by default.

## Getting Started

1. Clone the repository or download the script.

2. Open the script in a Python editor or IDE.

3. Replace the placeholder text in the following lines with your info.

4. Save the script.

5. Run the script using Python.

6. The Tailscale Manager window will open.

## Usage

1. Enter your Tailscale API key and the tailnet name in the provided entry fields.

2. Click the "Login" button to log in and fetch the list of devices associated with the specified tailnet.

3. Enter a search term in the search entry field to filter the device list. The list will update dynamically as you type.

4. Select one or more devices from the device list by clicking on them.

5. Click the "Select All Visible Devices" button to select all devices in the visible list.

6. Enter the tags you want to apply to the selected devices in the tag entry field. Separate multiple tags with commas.

7. Click the "Apply Tags" button to apply the selected tags to the selected devices.

8. If there is an error during the tag application process, an error message box will be displayed.

Note: You can resize the window according to your preference.

## License

This script is released under the [GNU General Public License v3.0](LICENSE).

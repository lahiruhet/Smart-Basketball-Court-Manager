import tinytuya
from config import DEVICES

# Function to check and print the status of a single device
def check_device_status(name, device_info):
    print(f"\nChecking status for {name}:")
    
    # Connect to the device
    device = tinytuya.OutletDevice(
        dev_id=device_info['id'],
        address=device_info['ip'],
        local_key=device_info['key'],
        version=3.4
    )
    
    # Fetch and print the device status
    status = device.status()
    if 'dps' in status and '1' in status['dps']:
        if status['dps']['1']:
            print(f'{name} is ON')
        else:
            print(f'{name} is OFF')
    else:
        print(f'Failed to retrieve status for {name}')

# Iterate through all devices and check their status
for name, info in DEVICES.items():
    check_device_status(name, info)

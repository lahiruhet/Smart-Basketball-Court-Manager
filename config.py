import os
from dotenv import load_dotenv

# Attempt to load the .env file
load_dotenv()

# Check if we're in production mode
IS_PRODUCTION = os.getenv('IS_PRODUCTION', 'false').lower() == 'true'

if IS_PRODUCTION:
    API_URL = os.getenv('API_URL')
    
    DEVICES = {
        'Half Court A': {
            'id': os.getenv('HALF_COURT_A_ID'),
            'ip': os.getenv('HALF_COURT_A_IP', 'Auto'),
            'key': os.getenv('HALF_COURT_A_KEY')
        },
        'Half Court B': {
            'id': os.getenv('HALF_COURT_B_ID'),
            'ip': os.getenv('HALF_COURT_B_IP', 'Auto'),
            'key': os.getenv('HALF_COURT_B_KEY')
        },
        'Full Court': {
            'id': os.getenv('FULL_COURT_ID'),
            'ip': os.getenv('FULL_COURT_IP', 'Auto'),
            'key': os.getenv('FULL_COURT_KEY')
        }
    }

    def setup_devices():
        import tinytuya
        devices = {}
        for court, info in DEVICES.items():
            try:
                device = tinytuya.BulbDevice(
                    dev_id=info['id'],
                    address=info['ip'],
                    local_key=info['key'],
                    version=3.4
                )
                device.set_version(3.4)
                devices[court] = device
                print(f"Device set up for {court}")
            except Exception as e:
                print(f"Error setting up device for {court}: {e}")
        return devices

    def check_device_status(device, expected_state):
        try:
            status = device.status()
            actual_state = status.get('dps', {}).get('1')
            if actual_state == expected_state:
                return True
            else:
                print(f"Device state mismatch. Expected: {expected_state}, Actual: {actual_state}")
                return False
        except Exception as e:
            print(f"Error checking device status: {e}")
            return False

else:
    # Test configuration
    API_URL = "http://127.0.0.1:5000/reservations"

    class DEVICES:
        def __init__(self, name):
            self.name = name
            self.state = False

        def turn_on(self):
            self.state = True
            print(f"{self.name} light turned ON")

        def turn_off(self):
            self.state = False
            print(f"{self.name} light turned OFF")

    def setup_devices():
        devices = {
            'Half Court A': DEVICES('Half Court A'),
            'Half Court B': DEVICES('Half Court B'),
            'Full Court': DEVICES('Full Court')
        }
        return devices

    def check_device_status(device, expected_state):
        actual_state = device.state
        if actual_state == expected_state:
            print(f"{device.name} status check passed.")
            return True
        else:
            print(f"{device.name} status check failed. Expected: {expected_state}, Actual: {actual_state}")
            return False

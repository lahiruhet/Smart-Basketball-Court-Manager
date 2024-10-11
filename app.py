import logging
from datetime import datetime, timedelta
import time
import requests
import schedule
import threading
import sys
import os
import signal

from config import API_URL, setup_devices, check_device_status

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variables
current_reservations = None
daily_routine_running = False
exit_flag = threading.Event()

def control_light(devices, half_a_on, half_b_on, full_on):
    try:
        lights_to_control = []
        failed_lights = []

        # Determine which lights need to be on or off
        lights_to_control.append(('Full Court', full_on or half_a_on or half_b_on))
        lights_to_control.append(('Half Court A', half_a_on))
        lights_to_control.append(('Half Court B', half_b_on))
        
        def attempt_light_operation(light, turn_on):
            operation = "on" if turn_on else "off"
            try:
                # Turn light on/off
                if turn_on:
                    devices[light].turn_on()
                else:
                    devices[light].turn_off()
                logging.info(f"{light} light turned {operation}")
                return True
            except Exception as e:
                logging.error(f"Error turning {operation} {light} light: {e}")
                return False

        def check_light_status(light, expected_state):
            try:
                status = check_device_status(devices[light], expected_state)
                if status is True:
                    logging.info(f"{light} light confirmed {'on' if expected_state else 'off'}")
                    return True
                elif status is False:
                    logging.warning(f"{light} light is in the wrong state")
                    return False
                else:  # status is None
                    logging.warning(f"Unable to confirm {light} light state")
                    return False
            except Exception as e:
                logging.error(f"Error checking {light} light status: {e}")
                return False

        # Process lights
        for light, should_be_on in lights_to_control:
            # Attempt to turn light on/off
            if attempt_light_operation(light, should_be_on):
                
                time.sleep(10)
                
                # Check light status
                if not check_light_status(light, should_be_on):
                    failed_lights.append((light, should_be_on))
                
                
                time.sleep(10)
            else:
                failed_lights.append((light, should_be_on))

        # Retry failed lights

        for light, should_be_on in failed_lights:
            logging.info(f"Retrying {light} light")
            if attempt_light_operation(light, should_be_on):
                
                time.sleep(10)
                
                if check_light_status(light, should_be_on):
                    logging.info(f"Successfully turned {light} light {'on' if should_be_on else 'off'} on retry")
                else:
                    logging.error(f"Failed to confirm {light} light state after retry")
            else:
                logging.error(f"Failed to turn {light} light {'on' if should_be_on else 'off'} on retry")

    except Exception as e:
        logging.error(f"Error controlling lights: {e}")

def convert_to_24hr(time_str):
    time_obj = datetime.strptime(time_str, "%I:%M %p")
    return time_obj.strftime("%H:%M")

def get_reservations_from_api():
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['reservations']
    except requests.RequestException as e:
        logging.error(f"Error fetching data from API: {e}")
        return None

def clean_court_names(reservations):
    return {
        time: [court.rstrip('.') for court in courts]
        for time, courts in reservations.items()
    }

def control_lights(devices, reservations):
    current_time = datetime.now()

    # Check if today is a weekend
    is_weekend = current_time.weekday() >= 5  # 5 is Saturday, 6 is Sunday

    if is_weekend:
        logging.info("Today is a weekend. Activating weekend schedule.")

        # Define the weekend morning activation period
        weekend_start_time = current_time.replace(hour=4, minute=30, second=0, microsecond=0)
        weekend_end_time = current_time.replace(hour=5, minute=30, second=0, microsecond=0)

        if current_time < weekend_start_time:
            wait_time = (weekend_start_time - current_time).total_seconds()
            logging.info(f"Waiting until {weekend_start_time.strftime('%H:%M')} to turn on lights for the weekend morning.")
            time.sleep(wait_time)
            current_time = datetime.now()  # Update current_time after sleep

        if weekend_start_time <= current_time < weekend_end_time:
            logging.info("Turning on all lights for the weekend morning period (04:30 - 05:30).")
            control_light(devices, True, True, True)
            while current_time < weekend_end_time:
                time.sleep(60)
                current_time = datetime.now()
            logging.info("Weekend morning period ended. Processing reservations.")
            current_time = datetime.now()  # Update current_time after sleep
    
    # Sort reservations by time
    sorted_reservations = sorted(reservations.items(), key=lambda x: datetime.strptime(x[0], "%H:%M"))

    # Find the earliest reservation time
    if sorted_reservations:
        earliest_reservation = datetime.strptime(sorted_reservations[0][0], "%H:%M").replace(
            year=current_time.year,
            month=current_time.month,
            day=current_time.day
        )
        if not is_weekend:
            # Calculate 15 minutes before the earliest reservation
            early_activation_time = earliest_reservation - timedelta(minutes=15)

            # If it's past midnight and before the early activation time, wait until then
            if current_time.time() < early_activation_time.time():
                wait_time = (early_activation_time - current_time).total_seconds()
                logging.info(f"Waiting until {early_activation_time.strftime('%H:%M')} to turn on lights for first reservation")
                time.sleep(wait_time)
                current_time = datetime.now()  # Update current_time after sleep
                control_light(devices, True, True, True)
                logging.info("Lights turned on for weekday early morning activation")
                while current_time < earliest_reservation:
                    time.sleep(60)
                    current_time = datetime.now()
                logging.info("Weekday morning period ended. Processing reservations.")
                current_time = datetime.now()  # Update current_time after sleep

    off_start_time = current_time.replace(hour=7, minute=30, second=0, microsecond=0)
    off_end_time = current_time.replace(hour=17, minute=30, second=0, microsecond=0)
    all_on_start_time = current_time.replace(hour=17, minute=30, second=0, microsecond=0)
    all_on_end_time = current_time.replace(hour=18, minute=30, second=0, microsecond=0)

    for reservation_time, courts in sorted_reservations:
        reservation_datetime = datetime.strptime(reservation_time, "%H:%M").replace(
            year=current_time.year,
            month=current_time.month,
            day=current_time.day
        )

        if current_time > reservation_datetime + timedelta(minutes=59):
            logging.info(f"Skipping reservation at {reservation_time} as it's passed")
            continue


        if off_start_time <= current_time < off_end_time:
            logging.info("Current time is within the off period (07:30 - 17:30). Turning off all lights.")
            control_light(devices, False, False, False)

            # Wait until the off period ends
            wait_time = (off_end_time - current_time).total_seconds()
            time.sleep(wait_time)
            logging.info("Off period ended. Resuming reservation processing.")
            current_time = datetime.now()  # Update current_time after sleep

        if all_on_start_time <= current_time < all_on_end_time:
            logging.info("Current time is within the all-on period (17:30 - 18:30). Turning on all lights.")
            control_light(devices, True, True, True)
                
            # Wait until the all-on period ends
            wait_time = (all_on_end_time - current_time).total_seconds()
            time.sleep(wait_time)
            current_time = datetime.now()  # Update current_time after sleep

        if reservation_datetime > current_time:
            control_light(devices, False, False, False)
            if all_on_start_time < reservation_datetime:
                wait_time = (all_on_start_time - current_time).total_seconds()
                next_on_time = all_on_start_time
            else:
                wait_time = (reservation_datetime - current_time).total_seconds()
                next_on_time = reservation_datetime
            logging.info(f"Waiting for {wait_time} seconds until next reservation at {next_on_time}")
            time.sleep(wait_time)
            current_time = datetime.now()  # Update current_time after sleep

        # Determine which lights should be on for this reservation
        half_a_on = 'Half Court A' in courts or 'Full Court' in courts
        half_b_on = 'Half Court B' in courts or 'Full Court' in courts
        full_on = 'Full Court' in courts

        # Control the lights based on the current reservation needs
        control_light(devices, half_a_on, half_b_on, full_on)

        logging.info(f"Reservation started at {reservation_time} for {', '.join(courts)}")

        end_time = reservation_datetime + timedelta(minutes=60)

        # Wait until the end of the current reservation
        while current_time < end_time:
            time.sleep(60)
            current_time = datetime.now()  # Update current_time after sleep

    logging.info("All reservations processed. Keeping some lights on for additional time.")
    control_light(devices, True, True, True)
    time.sleep(300)  # 5 minutes
    control_light(devices, False, False, True)
    time.sleep(600)  # Another 10 minutes
    control_light(devices, False, False, False)
    logging.info("All lights turned OFF after additional time")


def get_reservations_with_retry(max_retries=2, retry_delay=300):
    for attempt in range(max_retries):
        reservations = get_reservations_from_api()
        if reservations:
            return clean_court_names(reservations)
        logging.error(f"Failed to fetch reservations. Attempt {attempt + 1}/{max_retries}")
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    return None

def check_and_update_reservations():
    global current_reservations
    logging.info("Checking for updated reservations")
    new_reservations = get_reservations_with_retry()
    
    if new_reservations:
        if new_reservations != current_reservations:
            logging.info("Reservations have changed. Restarting the program.")
            current_reservations = new_reservations
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            logging.info("No changes in reservations")
    else:
        logging.error("Failed to fetch updated reservations")

def schedule_reservation_checks():
    schedule.every().day.at("05:20").do(check_and_update_reservations)
    schedule.every().day.at("06:20").do(check_and_update_reservations)
    schedule.every().day.at("18:20").do(check_and_update_reservations)
    schedule.every().day.at("19:20").do(check_and_update_reservations)
    schedule.every().day.at("20:20").do(check_and_update_reservations)
    schedule.every().day.at("21:20").do(check_and_update_reservations)

def run_scheduled_checks():
    while not exit_flag.is_set():
        schedule.run_pending()
        time.sleep(1)

def daily_routine():
    global current_reservations, daily_routine_running
    if daily_routine_running:
        logging.info("Daily routine is already running. Skipping.")
        return

    daily_routine_running = True
    logging.info(f"Starting daily routine at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        current_reservations = get_reservations_with_retry()
        
        if current_reservations:
            logging.info("Reservations fetched:")
            for reservation_time, courts in current_reservations.items():
                logging.info(f"Time: {reservation_time}, Courts: {', '.join(courts)}")
            
            devices = setup_devices()
            if not devices:
                logging.error("Failed to set up devices. Exiting.")
                return
            
            control_lights(devices, current_reservations)
            logging.info("Daily routine completed successfully")
        else:
            logging.error("Failed to fetch reservations. Skipping light control for today.")
    finally:
        daily_routine_running = False

def signal_handler(signum, frame):
    logging.info(f"Received signal {signum}. Exiting gracefully...")
    exit_flag.set()
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logging.info("Starting the court lighting management system")

    # Schedule reservation checks
    schedule_reservation_checks()
    logging.info("Reservation checks scheduled")

    # Start the thread for running scheduled checks
    check_thread = threading.Thread(target=run_scheduled_checks)
    check_thread.start()

    # Run the daily routine immediately
    daily_routine()
    
    # Schedule the daily routine to run at 4:10 AM every day
    schedule.every().day.at("04:10").do(daily_routine)
    logging.info("Daily routine scheduled to run at 04:10 AM")

    try:
        while not exit_flag.is_set():
            schedule.run_pending()
            time.sleep(60)
    except Exception as e:
        logging.error(f"An error occurred in the main loop: {e}")
    finally:
        logging.info("Exiting the application...")
        exit_flag.set()
        check_thread.join()

if __name__ == "__main__":
    main()


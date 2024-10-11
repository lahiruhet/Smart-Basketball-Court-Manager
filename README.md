# Smart Basketball Court Management System

## Overview

This project is an IoT solution for automating the lighting system of a high-traffic basketball court facility. Developed for a popular basketball hub in Colombo, Sri Lanka [LOLC Basketball Court](https://g.co/kgs/cJUwqWv), this system seamlessly integrates reservation management with smart lighting control, enhancing operational efficiency and user experience.

## Key Features

- **Automated Lighting Control**: Dynamically manages court lights based on real-time reservation data.
- **API Integration**: Fetches reservation data from a custom booking system API.
- **IoT Device Management**: Controls smart switches using the TinyTuya library.
- **Intelligent Scheduling**: 
  - Implements complex scheduling logic including early morning activations, off-hours, and extended operation times.
- **Fail-Safe Mechanisms**: Robust error handling and status checking for reliable operation.
- **Remote Monitoring**: Includes a web interface for real-time system status monitoring and manual control.

## Technical Stack

- **Backend**: Python
- **IoT Communication**: TinyTuya library
- **Web Interface**: Flask
- **Deployment**: Headless Raspberry Pi

## System Architecture

1. **Reservation Fetcher**: Periodically retrieves booking data from the API.
2. **Scheduler**: Manages the timing of light operations based on reservations and predefined rules.
3. **Device Controller**: Interfaces with IoT switches to control the physical lighting system.
4. **Status Monitor**: Continuously checks device statuses and implements retry mechanisms.
5. **Web Server**: Provides a user interface for monitoring and manual control.


## Setup and Configuration

### Prerequisites

- Python 3.7+
- pip (Python package manager)

### Required Libraries

Install the following libraries using pip:

```bash
pip install flask python-dotenv tinytuya schedule requests
```
### Clone this repository:
```
git clone https://github.com/yourusername/smart-basketball-court-management.git
cd smart-basketball-court-management
```
### Set up the environment:
a. If you have smart devices:

Create a .env file in the project root directory
Add the following configurations to the .env file:
```
IS_PRODUCTION=true
API_URL=https://your-api-endpoint.com
API_SECRET=your_api_secret
HALF_COURT_A_ID=device_id_for_half_court_a
HALF_COURT_A_IP=ip_for_half_court_a
HALF_COURT_A_KEY=device_key_for_half_court_a
HALF_COURT_B_ID=device_id_for_half_court_b
HALF_COURT_B_IP=ip_for_half_court_b
HALF_COURT_B_KEY=device_key_for_half_court_b
FULL_COURT_ID=device_id_for_full_court
FULL_COURT_IP=ip_for_full_court
FULL_COURT_KEY=device_key_for_full_court
```
Replace the placeholder values with your actual device and API configurations

b. If you don't have smart devices:

You can use the mock setup included in the project.
Create a .env file and set:
```
IS_PRODUCTION=false
API_URL=https://your-api-endpoint.com
```

This will use simulated devices for testing purposes

### Running the Project

Start the web interface and the main application:
```
python web.py
```




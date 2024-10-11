from flask import Flask, render_template, redirect, url_for, jsonify
import subprocess
import threading
import time
from collections import deque
import io

app = Flask(__name__)
log_buffer = deque(maxlen=1000)  # Adjust this number to control how many log lines to keep
log_lock = threading.Lock()

script_process = None

def kill_existing_process():
    global script_process
    if script_process:
        script_process.terminate()
        script_process.wait()

def run_script():
    global script_process, log_buffer
    
    kill_existing_process()
    
    try:
        script_process = subprocess.Popen(
            ["python", "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        for line in iter(script_process.stdout.readline, ''):
            with log_lock:
                log_buffer.append(line.strip())
        
        script_process.stdout.close()
        script_process.wait()
    except Exception as e:
        with log_lock:
            log_buffer.append(f"Error starting app.py: {str(e)}")

@app.route('/')
def index():
    with log_lock:
        log = '\n'.join(log_buffer)
    return render_template('index.html', log=log)

@app.route('/restart')
def restart_script():
    thread = threading.Thread(target=run_script)
    thread.start()
    return redirect(url_for('index'))

@app.route('/get_logs')
def get_logs():
    with log_lock:
        log = '\n'.join(log_buffer)
    return jsonify(log=log)

if __name__ == '__main__':
    thread = threading.Thread(target=run_script)
    thread.start()
    app.run(host='0.0.0.0', port=5001, debug=False)  # Note: debug mode is now off

import time
import subprocess
import platform
from dotenv import load_dotenv
from constants import send_email

load_dotenv()


def send_crash_email(script_name, error_msg):
    msg = (
        f"Subject: {script_name} Crashed & Restarted!\n\n"
        f"The {script_name} encountered an error:\n{error_msg}\n\n"
        f"Restarting...\n\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    send_email(msg)


processes = {
    "main_v2.py": None,
    "get_price_data_v3.py": None
}


def start_process(script_name):
    print(f"Starting {script_name}")

    if platform.system() == "Windows":
        return subprocess.Popen(["python", script_name],
                                creationflags=subprocess.CREATE_NEW_CONSOLE)
    elif platform.system() == "Linux":
        return subprocess.Popen(["python3", script_name], stdout=None, stderr=None)

    else:
        return subprocess.Popen(["python", script_name])


# Start all processes initially
for script in processes.keys():
    processes[script] = start_process(script)

while True:
    for script, process in processes.items():
        if process.poll() is not None:
            error_output = process.communicate()
            error_message = error_output if error_output else f"{script} stopped unexpectedly"
            send_crash_email(script, error_message)
            processes[script] = start_process(script)
            time.sleep(2)

    time.sleep(5)

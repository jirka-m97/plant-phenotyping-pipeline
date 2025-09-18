# =========================================================================
# Arduino CLI Compile & Upload Helper (Python, en-GB)
# Author: Jiří Mach
# Institution: UCT Prague, Laboratory of Bioengineering
# Licence: Apache 2.0
# Date: 2025-09-18
# Description:
#   Provides a Python wrapper for the Arduino CLI toolchain. The function
#   `upload_arduino()` compiles and uploads an Arduino sketch (*.ino) to a
#   specified board (default: Arduino Uno) via a given serial port.
#   Compilation and upload are executed as subprocesses with console
#   output redirected to Python for easier debugging.
# Dependencies:
#   Python stdlib: subprocess
#   External: arduino-cli (https://arduino.github.io/arduino-cli/)

import subprocess

def upload_arduino(arduino_file, port="COM5", fqbn="arduino:avr:uno", arduino_cli_dir=r".\Arduino_cli"):
    arduino_cli_path = arduino_cli_dir + r".\arduino-cli.exe"

    def run_command(cmd, cwd):
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print("Error:", result.stderr)
        return result.returncode == 0

    print("Compiling...")
    if not run_command([arduino_cli_path, "compile", "--fqbn", fqbn, arduino_file], arduino_cli_dir):
        print("Compilation failed!")
        return False

    print("Uploading...")
    if not run_command([arduino_cli_path, "upload", "-p", port, "--fqbn", fqbn, arduino_file], arduino_cli_dir):
        print("Upload failed!")
        return False

    print("Done.")
    return True

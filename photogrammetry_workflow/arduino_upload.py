import subprocess

def upload_arduino(arduino_file, port="COM5", fqbn="arduino:avr:uno", arduino_cli_dir=r"C:\Users\Student\Desktop\Arduino_cli"):
    arduino_cli_path = arduino_cli_dir + r"\arduino-cli.exe"

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

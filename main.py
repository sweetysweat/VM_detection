import subprocess
import os
import requests


"""Here you can see all signs of VM"""
VM_signs = {
    "Internet Connection:": "",
    "MAC:": "",
}
count_signs = 0


def execute_command(command: list[str]) -> list[str]:
    """Run command in shell and save it for parsing"""
    data = []
    for line in subprocess.Popen(["Powershell.exe", *command], stdout=subprocess.PIPE).stdout:
        if line.strip():
            data.append(line.decode("cp866").strip())
    return data


def check_internet_connection():
    """Check Internet connection"""
    global count_signs
    try:
        requests.get("https://www.google.com/", timeout=5)
        VM_signs["Internet Connection:"] = "Yes"
    except requests.ConnectionError:
        VM_signs["Internet Connection:"] = "No"
        count_signs += 1


def get_MAC():
    """Run ipconfig in shell and find MAC"""
    global count_signs
    for row in execute_command(["ipconfig", "/all"]):
        row = row.split()
        if row[0] in ["Физический", "Physical"]:
            if row[-1].startswith("00-0C-29"):
                VM_signs["MAC:"] = f"{row[-1]} - standard VMware MAC"
                count_signs += 1
            else:
                VM_signs["MAC:"] = "Real MAC"
            break


if __name__ == "__main__":
    check_internet_connection()
    get_MAC()


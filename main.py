import subprocess
import re
import requests


"""Here you can see all signs of VM"""
VM_signs = {
    "Internet Connection": "",
    "MAC": "",
    "Machine model": "",
    "BIOS": "",
    "Services": "",
}
count_signs = 0
pattern = r"\b[Vv][Mm]ware\b|[Vv][Mm]"  # Pattern for detecting VM or VMware in a string


def check_internet_connection():
    """Check Internet connection"""
    global count_signs
    try:
        requests.get("https://www.google.com/", timeout=5)
        VM_signs["Internet Connection"] = "Yes"
    except requests.ConnectionError:
        VM_signs["Internet Connection"] = "No"
        count_signs += 1


def execute_command(command: list[str]) -> str:
    """Run command in shell"""
    return subprocess.Popen(["Powershell.exe", *command], stdout=subprocess.PIPE).stdout.read().decode("cp866")


def get_MAC():
    """Runs ipconfig in shell and find MAC"""
    global count_signs
    data = execute_command(["ipconfig", "/all"]).split()
    for row in data:
        row = row.split()
        if row[0] in ["Физический", "Physical"]:
            if row[-1].startswith("00-0C-29"):
                VM_signs["MAC"] = f"{row[-1]} - standard VMware MAC"
                count_signs += 1
            else:
                VM_signs["MAC"] = "Real MAC"
            break


def get_Model():
    """Runs get-wmiobject win32_computersystem | fl Model in shell to get model of machine"""
    global count_signs
    data = execute_command(["get-wmiobject", "win32_computersystem",
                            "|", "fl", "model"]).strip().split()[-1]  # -1 to get only model
    if re.search(pattern, data):
        VM_signs["Machine model"] = data
        count_signs += 1
    else:
        VM_signs["Machine model"] = "Unique model"


def get_BIOS():
    global count_signs
    data = execute_command(["Get-CimInstance", "-ClassName", "Win32_BIOS",
                            "|", "fl", "Manufacturer"]).strip().split()[-1]  # get only vendor
    if re.search(pattern, data):
        VM_signs["BIOS"] = data
        count_signs += 1
    else:
        VM_signs["BIOS"] = "Standard BIOS vendor"


def get_Services():
    global count_signs
    data = execute_command(["Get-CimInstance", "-ClassName", "Win32_Service",
                            "|", "Select-Object", "-Property", "DisplayName"]).strip().split("\n")
    for row in data:
        if re.search(pattern, row):
            VM_signs["Services"] = f"Found - {row}"
            count_signs += 1
            break
    else:
        VM_signs["Services"] = "No VMware services"


if __name__ == "__main__":
    check_internet_connection()
    get_MAC()
    get_Model()
    get_BIOS()
    get_Services()
    for k, v in VM_signs.items():
        print(f"{k}: {v}")

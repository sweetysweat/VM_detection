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
    "Devices": "",
    "VM Tools in processes": ""
}
count_signs = 0
pattern = r"\b[Vv][Mm]ware\b|[V][M]"  # Pattern for detecting VM or VMware in a string


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
    """Run Get-CimInstance, -ClassName Win32_BIOS | fl Manufacturer to get BIOS model"""
    global count_signs
    data = execute_command(["Get-CimInstance", "-ClassName", "Win32_BIOS",
                            "|", "fl", "Manufacturer"]).strip().split()[-1]  # get only vendor
    if re.search(pattern, data):
        VM_signs["BIOS"] = data
        count_signs += 1
    else:
        VM_signs["BIOS"] = "Standard BIOS vendor"


def get_Services():
    """Run Get-CimInstance -ClassName Win32_Service | Select-Object -Property DisplayName to get windows services"""
    global count_signs
    hosts_vmware_services = ["VMware Authorization Service", "VMware DHCP Service", "VMware USB Arbitration Service",
                             "VMware NAT Service", "VMware Workstation Server"]
    data = execute_command(["Get-CimInstance", "-ClassName", "Win32_Service",
                            "|", "Select-Object", "-Property", "DisplayName"]).strip().split("\n")
    for row in data:
        row = row.strip()
        if re.search(pattern, row) and row not in hosts_vmware_services:
            VM_signs["Services"] = f"Found - {row}"
            count_signs += 1
            break
    else:
        VM_signs["Services"] = "No VMware services"


def get_Devices():
    """Run gwmi Win32_PnPSignedDriver | select devicename to get devices"""
    global count_signs
    guest_vmware_devices = ["VMware VMCI Host Device", "VMware USB Pointing Device",
                            "VMware SVGA 3D", "VMware VMCI Bus Device", "VMware Pointing Device"]
    data = execute_command(["gwmi", "Win32_PnPSignedDriver", "|", "select", "devicename"]).strip().split("\n")
    for row in data:
        if re.search(pattern, row) and row in guest_vmware_devices:
            VM_signs["Devices"] = f"Found - {row}"
            count_signs += 1
            break
    else:
        VM_signs["Devices"] = "No VMware devices"


def get_processes():
    """Run Get-Process | fl ProcessName to get all running processes to find VM Tools"""
    global count_signs
    data = execute_command(["Get-Process", "|", "fl", "ProcessName"])
    for row in data:
        if row[-1] == "vmtoolssd":
            VM_signs["VM Tools in processes"] = "Found"
            count_signs += 1
            break
    else:
        VM_signs["VM Tools in processes"] = "Not Found"


if __name__ == "__main__":
    check_internet_connection()
    get_MAC()
    get_Model()
    get_BIOS()
    get_Services()
    get_Devices()
    get_processes()
    for k, v in VM_signs.items():
        print(f"{k}: {v}")

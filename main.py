import subprocess
import re
import os

"""Here you can see all signs of VM"""
VM_signs = {
    "Internet Connection": "",
    "MAC": "",
    "Machine model": "",
    "BIOS": "",
    "Services": "",
    "Devices": "",
    "VM Tools in processes": "",
    "CPU cores": "",
    "RAM memory": "",
    "Memory": "",
    "Directory": "",
}
count_signs = 0
pattern = r"\b[Vv][Mm]ware\b|[V][M]"  # Pattern for detecting VM or VMware in a string


def execute_command(command: list[str]) -> str:
    """Run command in shell"""
    return subprocess.Popen(["Powershell.exe", *command], stdout=subprocess.PIPE).stdout.read().decode("cp866")


def check_internet_connection():
    """Check Internet connection"""
    global count_signs
    data = execute_command(["ping 8.8.8.8"]).strip().split()
    for element in data:
        if "%" in element:
            ping_success = element[1:-1]
            if int(ping_success) < 100:
                count_signs += 1
                VM_signs["Internet Connection"] = f"Yes, {ping_success}% packets lost"
            else:
                VM_signs["Internet Connection"] = f"No"
            break


def get_MAC():
    """Runs ipconfig in shell and find MAC"""
    global count_signs
    data = execute_command(["ipconfig /all"]).split("\n")
    for row in data:
        if any(element in row for element in ["Физический", "Physical"]):
            data = row.split()[-1].strip()
            if data.startswith("00-0C-29"):
                count_signs += 1
                VM_signs["MAC"] = f"{data} - standard VMware MAC"
                break
    else:
        VM_signs["MAC"] = "Real MAC"


def get_model():
    """Runs get-wmiobject win32_computersystem | fl Model in shell to get model of machine"""
    global count_signs
    data = execute_command(["get-wmiobject win32_computersystem | fl model"]) \
        .strip().split()[-1]  # -1 to get only model
    if re.search(pattern, data):
        VM_signs["Machine model"] = data
        count_signs += 1
    else:
        VM_signs["Machine model"] = "Unique model"


def get_BIOS():
    """Run Get-CimInstance, -ClassName Win32_BIOS | fl Manufacturer to get BIOS model"""
    global count_signs
    data = execute_command(["Get-CimInstance -ClassName Win32_BIOS | fl Manufacturer"]).strip()
    vendor = data[data.find(":") + 1:].strip()
    if re.search(pattern, vendor):
        VM_signs["BIOS"] = f"Vendor is {vendor}"
        count_signs += 1
    else:
        VM_signs["BIOS"] = "Standard BIOS vendor"


def get_services():
    """Run Get-CimInstance -ClassName Win32_Service | Select-Object -Property DisplayName to get windows services"""
    global count_signs
    hosts_vmware_services = ["VMware Authorization Service", "VMware DHCP Service", "VMware USB Arbitration Service",
                             "VMware NAT Service", "VMware Workstation Server"]
    data = execute_command(["Get-CimInstance -ClassName Win32_Service | Select-Object -Property DisplayName"]) \
        .strip().split("\n")
    for row in data:
        row = row.strip()
        if re.search(pattern, row) and row not in hosts_vmware_services:
            VM_signs["Services"] = f"Found - {row}"
            count_signs += 1
            break
    else:
        VM_signs["Services"] = "No VMware services"


def get_devices():
    """Run gwmi Win32_PnPSignedDriver | select devicename to get devices"""
    global count_signs
    guest_vmware_devices = ["VMware VMCI Host Device", "VMware USB Pointing Device",
                            "VMware SVGA 3D", "VMware VMCI Bus Device", "VMware Pointing Device"]
    data = execute_command(["gwmi Win32_PnPSignedDriver | select devicename"]).strip().split("\n")
    for row in data:
        row = row.strip()
        if re.search(pattern, row) and row in guest_vmware_devices:
            VM_signs["Devices"] = f"Found - {row}"
            count_signs += 1
            break
    else:
        VM_signs["Devices"] = "No VMware devices"


def get_processes():
    """Run Get-Process | fl ProcessName to get all running processes to find VM Tools"""
    global count_signs
    data = execute_command(["Get-Process | fl ProcessName"]).strip().split("\n")
    for row in data:
        if "vmtoolsd" in row:
            VM_signs["VM Tools in processes"] = "Found"
            count_signs += 1
            break
    else:
        VM_signs["VM Tools in processes"] = "Not found"


def get_CPU():
    """Run wmic cpu get NumberOfCores to get amount of CPU cores"""
    global count_signs
    data = execute_command(["wmic cpu get NumberOfCores"]).strip()[-1]
    if int(data) < 4:
        count_signs += 1
        VM_signs["CPU cores"] = f"Too few cores - {data}"
    else:
        VM_signs["CPU cores"] = f"{data} cores"


def get_RAM():
    """
    Run (Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum).sum /1gb to get RAM memory
    """
    global count_signs
    data = execute_command(["(Get-CimInstance Win32_PhysicalMemory |"
                            " Measure-Object -Property capacity -Sum).sum /1gb"]).strip()
    if int(data) < 8:
        count_signs += 1
        VM_signs["RAM memory"] = f"Too few memory - {data}GB"
    else:
        VM_signs["RAM memory"] = f"{data}GB of RAM memory"


def get_disk_size():
    """
    Run Get-CimInstance -ClassName Win32_LogicalDisk | Select-Object -Property DeviceID,@{'Name' = 'FreeSpace (GB)';\
    Expression= { [int]($_.Size / 1GB) }} to check all disks size
    """
    global count_signs
    memory = 0
    data = execute_command(["Get-CimInstance -ClassName Win32_LogicalDisk | Select-Object -Property DeviceID,"
                            "@{'Name' = 'FreeSpace (GB)';Expression= { [int]($_.Size / 1GB) }}"]).strip().split()[5:]
    for disk_info in data:
        if disk_info.isdigit():
            memory += int(disk_info)
    if memory < 64:
        count_signs += 1
        VM_signs["Memory"] = f"Too few memory - {memory}GB"
    else:
        VM_signs["Memory"] = f"{memory}GB - disks space"


def find_directory():
    """Search VMware folder in C:\Program Files"""
    global count_signs
    for directory in os.listdir("C:\Program Files"):
        if directory == "VMware":
            count_signs += 1
            VM_signs["Directory"] = f"{directory} is found"
            break
    else:
        VM_signs["Directory"] = "Nothing was found"


if __name__ == "__main__":
    check_internet_connection()
    get_MAC()
    get_model()
    get_BIOS()
    get_services()
    get_devices()
    get_processes()
    get_CPU()
    get_RAM()
    get_disk_size()
    find_directory()
    for k, v in VM_signs.items():
        print(f"{k}: {v}")
    print(f"Probability: {round(count_signs / len(VM_signs) * 100, 2)}%")

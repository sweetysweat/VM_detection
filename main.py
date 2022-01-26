import os
import re
import socket
import subprocess
import winreg


class VMDetection:
    def __init__(self):
        """Here you can see all signs of VM. This signs will change value if something is going to be found."""
        self.VM_signs = {
            "Internet Connection": "Yes",
            "MAC": "Real MAC",
            "Machine model": "Unique model",
            "BIOS": "Standard BIOS vendor",
            "Services": "No VMware services",
            "Devices": "No VMware devices",
            "VM Tools in processes": "Not found",
            "CPU cores": "More or exactly 4 cores",
            "RAM memory": "More or exactly 8 GB of RAM",
            "Memory": "more or exactly 64 GB",
            "Directory": "Nothing was found",
            "Drivers": "Nothing was found",
            "Registry": "Nothing found",
        }
        self.count_signs = 0
        self.pattern = r"\b[Vv][Mm]ware\b|[V][M]"  # Pattern for detecting VM or VMware in a string
        """
        In future this programme is going to be an console application (.exe).
        So, you should run it and program will give answer.
        """
        self.check_internet_connection()
        self.get_MAC()
        self.get_model()
        self.get_BIOS()
        self.get_services()
        self.get_devices()
        self.get_processes()
        self.get_CPU()
        self.get_RAM()
        self.get_disk_size()
        self.find_directory()
        self.get_drivers()
        self.get_registry()
        self.get_result()

    @staticmethod
    def execute_command(command: str) -> str:
        """Run command in shell"""
        return subprocess.Popen(["Powershell.exe", command], stdout=subprocess.PIPE).stdout.read().decode("cp866")

    def check_internet_connection(self):
        """Check Internet connection"""
        id_address_list = [
            "1.1.1.1",  # Cloudflare
            "1.0.0.1",
            "8.8.8.8",  # Google DNS
            "8.8.4.4",
        ]
        for host in id_address_list:
            try:
                socket.create_connection((host, 53))  # 53 is a port for DOMAIN (DNS)
                break
            except socket.error:
                pass
        else:
            self.count_signs += 1
            print(self.count_signs)
            self.VM_signs["Internet Connection"] = "No"

    def get_MAC(self):
        """Runs ipconfig in shell and find MAC"""
        data = self.execute_command("ipconfig /all").split("\n")
        for row in data:
            if any(element in row for element in ["Физический", "Physical"]):
                data = row.split()[-1].strip()
                if data.startswith("00-0C-29"):
                    self.count_signs += 1
                    self.VM_signs["MAC"] = f"{data} - standard VMware MAC"
                    break

    def get_model(self):
        """Runs get-wmiobject win32_computersystem | fl Model in shell to get model of machine"""
        model = self.execute_command("get-wmiobject win32_computersystem | fl model") \
                    .strip()[8:]  # [8:] to ignore "model : " to get only useful information
        if re.search(self.pattern, model):
            self.VM_signs["Machine model"] = model
            self.count_signs += 1

    def get_BIOS(self):
        """Run Get-CimInstance, -ClassName Win32_BIOS | fl Manufacturer to get BIOS model"""
        vendor = self.execute_command("Get-CimInstance -ClassName Win32_BIOS | fl Manufacturer").strip()[15:]
        if re.search(self.pattern, vendor) or "Phoenix Technologies LTD" in vendor:
            self.VM_signs["BIOS"] = f"Vendor is {vendor}"
            self.count_signs += 1

    def get_services(self):
        """Run Get-CimInstance -ClassName Win32_Service | Select-Object -Property DisplayName to get windows services"""
        hosts_vmware_services = ["VMware Authorization Service", "VMware DHCP Service",
                                 "VMware USB Arbitration Service",
                                 "VMware NAT Service", "VMware Workstation Server"]
        data = self.execute_command("Get-CimInstance -ClassName Win32_Service | Select-Object -Property DisplayName") \
            .strip().split("\n")
        for row in data:
            row = row.strip()
            if re.search(self.pattern, row) and row not in hosts_vmware_services:
                self.VM_signs["Services"] = f"Found - {row}"
                self.count_signs += 1
                break

    def get_devices(self):
        """Run gwmi Win32_PnPSignedDriver | select devicename to get devices unique for VMs"""
        guest_vmware_devices = ["VMware USB Pointing Device", "VMware SVGA 3D", "VMware VMCI Bus Device",
                                "VMware Pointing Device"]
        data = self.execute_command("gwmi Win32_PnPSignedDriver | select devicename").strip().split("\n")
        for row in data:
            row = row.strip()
            if re.search(self.pattern, row) and row in guest_vmware_devices:
                self.VM_signs["Devices"] = f"Found - {row}"
                self.count_signs += 1
                break

    def get_processes(self):
        """Run Get-Process | fl ProcessName to get all running processes to find VM Tools"""
        data = self.execute_command("Get-Process | fl ProcessName").strip().split("\n")
        for process in data:
            if "vmtoolsd" in process:
                self.VM_signs["VM Tools in processes"] = "Found"
                self.count_signs += 1
                break

    def get_CPU(self):
        """Run wmic cpu get NumberOfCores to get amount of CPU cores"""
        data = self.execute_command("wmic cpu get NumberOfCores").strip()[-1]
        if int(data) < 4:
            self.count_signs += 1
            self.VM_signs["CPU cores"] = f"Too few cores - {data}"

    def get_RAM(self):
        """
        Run (Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum).sum /1gb to get RAM memory
        """
        data = self.execute_command("(Get-CimInstance Win32_PhysicalMemory |"
                                    " Measure-Object -Property capacity -Sum).sum /1gb").strip()
        if int(data) < 8:
            self.count_signs += 1
            self.VM_signs["RAM memory"] = f"Too few memory - {data}GB"

    def get_disk_size(self):
        """
        Run Get-CimInstance -ClassName Win32_LogicalDisk | Select-Object -Property DeviceID,@{'Name' =
        'FreeSpace (GB)'; Expression= { [int]($_.Size / 1GB) }} to check all disks size
        """
        memory = 0
        data = self.execute_command("Get-CimInstance -ClassName Win32_LogicalDisk | Select-Object -Property DeviceID,"
                                    "@{'Name' = 'FreeSpace (GB)';Expression= { [int]($_.Size / 1GB) }}") \
                   .strip().split()[5:]
        for disk_info in data:
            if disk_info.isdigit():
                memory += int(disk_info)
        if memory < 64:
            self.count_signs += 1
            self.VM_signs["Memory"] = f"Too few memory - {memory}GB"

    def find_directory(self):
        """Search VMware folder in C:\Program Files"""
        for directory in os.listdir("C:\Program Files"):
            if directory == "VMware":
                self.count_signs += 1
                self.VM_signs["Directory"] = f"{directory} is found"
                break

    def get_drivers(self):
        """Search VMware drivers unique for VMs"""
        drivers = ["vmmouse.sys", "vmhgfs.sys"]
        for file in os.listdir("C:\Windows\System32\drivers"):
            if file in drivers:
                self.count_signs += 1
                self.VM_signs["Drivers"] = "Drivers from VMware found"
                break

    def get_registry(self):
        """Search VMware register entries. registry_path contains only unique values for VM"""
        registry_path = [
            "SOFTWARE\\VMware, Inc.\\VMware Tools",
            "SYSTEM\\ControlSet001\\Services\\vmmouse",
            "SYSTEM\\ControlSet001\\Services\\VMTools",
            "SYSTEM\\ControlSet001\\Services\\VMMemCtl"
        ]
        for path in registry_path:
            try:
                winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                self.count_signs += 1
                self.VM_signs["Registry"] = "Register entries from VMware found"
                break
            except WindowsError:
                pass

    def get_result(self):
        for key, value in self.VM_signs.items():
            print(f"{key}: {value}")
        print(f"Probability: {round(self.count_signs / len(self.VM_signs) * 100, 2)}%")


if __name__ == "__main__":
    VM_Detection = VMDetection()

import subprocess
import re
import os


class VMDetection:
    def __init__(self):
        """Here you can see all signs of VM"""
        self.VM_signs = {
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
        self.count_signs = 0
        self.pattern = r"\b[Vv][Mm]ware\b|[V][M]"  # Pattern for detecting VM or VMware in a string
        """
        In future this programme is going to be an console application (.exe).
        So, you should run it and give answer
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
        self.get_result()

    @staticmethod
    def execute_command(command: list[str]) -> str:
        """Run command in shell"""
        return subprocess.Popen(["Powershell.exe", *command], stdout=subprocess.PIPE).stdout.read().decode("cp866")

    def check_internet_connection(self):
        """Check Internet connection"""
        data = self.execute_command(["ping 8.8.8.8"]).strip().split()
        for element in data:
            if "%" in element:
                ping_success = element[1:-1]
                if int(ping_success) < 100:
                    self.count_signs += 1
                    self.VM_signs["Internet Connection"] = f"Yes, {ping_success}% packets lost"
                else:
                    self.VM_signs["Internet Connection"] = f"No"
                break

    def get_MAC(self):
        """Runs ipconfig in shell and find MAC"""
        data = self.execute_command(["ipconfig /all"]).split("\n")
        for row in data:
            if any(element in row for element in ["Физический", "Physical"]):
                data = row.split()[-1].strip()
                if data.startswith("00-0C-29"):
                    self.count_signs += 1
                    self.VM_signs["MAC"] = f"{data} - standard VMware MAC"
                    break
        else:
            self.VM_signs["MAC"] = "Real MAC"

    def get_model(self):
        """Runs get-wmiobject win32_computersystem | fl Model in shell to get model of machine"""
        data = self.execute_command(["get-wmiobject win32_computersystem | fl model"]) \
            .strip().split()[-1]  # -1 to get only model
        if re.search(self.pattern, data):
            self.VM_signs["Machine model"] = data
            self.count_signs += 1
        else:
            self.VM_signs["Machine model"] = "Unique model"

    def get_BIOS(self):
        """Run Get-CimInstance, -ClassName Win32_BIOS | fl Manufacturer to get BIOS model"""
        data = self.execute_command(["Get-CimInstance -ClassName Win32_BIOS | fl Manufacturer"]).strip()
        vendor = data[data.find(":") + 1:].strip()
        if re.search(self.pattern, vendor):
            self.VM_signs["BIOS"] = f"Vendor is {vendor}"
            self.count_signs += 1
        else:
            self.VM_signs["BIOS"] = "Standard BIOS vendor"

    def get_services(self):
        """Run Get-CimInstance -ClassName Win32_Service | Select-Object -Property DisplayName to get windows services"""
        hosts_vmware_services = ["VMware Authorization Service", "VMware DHCP Service",
                                 "VMware USB Arbitration Service",
                                 "VMware NAT Service", "VMware Workstation Server"]
        data = self.execute_command(["Get-CimInstance -ClassName Win32_Service | Select-Object -Property DisplayName"]) \
            .strip().split("\n")
        for row in data:
            row = row.strip()
            if re.search(self.pattern, row) and row not in hosts_vmware_services:
                self.VM_signs["Services"] = f"Found - {row}"
                self.count_signs += 1
                break
        else:
            self.VM_signs["Services"] = "No VMware services"

    def get_devices(self):
        """Run gwmi Win32_PnPSignedDriver | select devicename to get devices"""
        global count_signs
        guest_vmware_devices = ["VMware VMCI Host Device", "VMware USB Pointing Device",
                                "VMware SVGA 3D", "VMware VMCI Bus Device", "VMware Pointing Device"]
        data = self.execute_command(["gwmi Win32_PnPSignedDriver | select devicename"]).strip().split("\n")
        for row in data:
            row = row.strip()
            if re.search(self.pattern, row) and row in guest_vmware_devices:
                self.VM_signs["Devices"] = f"Found - {row}"
                self.count_signs += 1
                break
        else:
            self.VM_signs["Devices"] = "No VMware devices"

    def get_processes(self):
        """Run Get-Process | fl ProcessName to get all running processes to find VM Tools"""
        data = self.execute_command(["Get-Process | fl ProcessName"]).strip().split("\n")
        for row in data:
            if "vmtoolsd" in row:
                self.VM_signs["VM Tools in processes"] = "Found"
                self.count_signs += 1
                break
        else:
            self.VM_signs["VM Tools in processes"] = "Not found"

    def get_CPU(self):
        """Run wmic cpu get NumberOfCores to get amount of CPU cores"""
        data = self.execute_command(["wmic cpu get NumberOfCores"]).strip()[-1]
        if int(data) < 4:
            self.count_signs += 1
            self.VM_signs["CPU cores"] = f"Too few cores - {data}"
        else:
            self.VM_signs["CPU cores"] = f"{data} cores"

    def get_RAM(self):
        """
        Run (Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum).sum /1gb to get RAM memory
        """
        data = self.execute_command(["(Get-CimInstance Win32_PhysicalMemory |"
                                     " Measure-Object -Property capacity -Sum).sum /1gb"]).strip()
        if int(data) < 8:
            self.count_signs += 1
            self.VM_signs["RAM memory"] = f"Too few memory - {data}GB"
        else:
            self.VM_signs["RAM memory"] = f"{data}GB of RAM memory"

    def get_disk_size(self):
        """
        Run Get-CimInstance -ClassName Win32_LogicalDisk | Select-Object -Property DeviceID,@{'Name' = 'FreeSpace (GB)';\
        Expression= { [int]($_.Size / 1GB) }} to check all disks size
        """
        memory = 0
        data = self.execute_command(["Get-CimInstance -ClassName Win32_LogicalDisk | Select-Object -Property DeviceID,"
                                     "@{'Name' = 'FreeSpace (GB)';Expression= { [int]($_.Size / 1GB) }}"]).strip().split()[
               5:]
        for disk_info in data:
            if disk_info.isdigit():
                memory += int(disk_info)
        if memory < 64:
            self.count_signs += 1
            self.VM_signs["Memory"] = f"Too few memory - {memory}GB"
        else:
            self.VM_signs["Memory"] = f"{memory}GB - disks space"

    def find_directory(self):
        """Search VMware folder in C:\Program Files"""
        for directory in os.listdir("C:\Program Files"):
            if directory == "VMware":
                self.count_signs += 1
                self.VM_signs["Directory"] = f"{directory} is found"
                break
        else:
            self.VM_signs["Directory"] = "Nothing was found"

    def get_result(self):
        for key, value in self.VM_signs.items():
            print(f"{key}: {value}")
        print(f"Probability: {round(self.count_signs / len(self.VM_signs) * 100, 2)}%")


if __name__ == "__main__":
    VM_Detection = VMDetection()

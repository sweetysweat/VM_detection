import requests
import subprocess

"""Here you can see all signs of VM"""
VM_signs = {
    "Internet Connection": "",
}


def check_internet_connection():
    """Check Internet connection"""
    try:
        requests.get("https://www.google.com/", timeout=5)
        VM_signs["Internet Connection"] = "Yes"
    except requests.ConnectionError:
        VM_signs["Internet Connection"] = "No"


if __name__ == "__main__":
    print(check_internet_connection())

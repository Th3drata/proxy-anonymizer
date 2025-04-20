#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_root():
    if os.geteuid() != 0:
        print("This script must be run as root. Please use sudo.")
        sys.exit(1)

def detect_os():
    try:
        import platform
        import distro
        if platform.system() == "Linux":
            distro_id = distro.id().lower()
            if distro_id in ["ubuntu", "debian", "kali"]:
                return "debian"
            elif distro_id == "arch":
                return "arch"
            elif distro_id in ["fedora", "centos", "rhel"]:
                return "rhel"
        return "unknown"
    except Exception:
        return "unknown"

def install_dependencies():
    os_type = detect_os()
    try:
        if os_type == "arch":
            subprocess.check_call('sudo pacman -Sy --noconfirm python python-pip tor gnu-netcat', shell=True)
        elif os_type == "debian":
            subprocess.check_call('sudo apt update && sudo apt install -y python3 python3-pip tor netcat', shell=True)
        elif os_type == "rhel":
            subprocess.check_call('sudo dnf install -y python3 python3-pip tor nmap-ncat', shell=True)
        else:
            print("Unsupported OS. Please install dependencies manually.")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install system dependencies: {e}")
        sys.exit(1)

def install_python_packages():
    os_type = detect_os()
    try:
        if os_type == "arch":
            try:
                with open('requirements.txt', 'r') as f:
                    packages = f.read().splitlines()
                    for package in packages:
                        if package.strip() and not package.startswith('#'):
                            pkg_name = package.split('>=')[0].strip()
                            arch_pkg = {
                                'requests': 'python-requests',
                                'beautifulsoup4': 'python-beautifulsoup4',
                                'distro': 'python-distro'
                            }.get(pkg_name, f'python-{pkg_name}')
                            
                            try:
                                subprocess.check_call(['sudo', 'pacman', '-S', '--noconfirm', arch_pkg])
                            except subprocess.CalledProcessError as e:
                                print(f"Failed to install {arch_pkg}: {e}")
                                print("Please install it manually using:")
                                print(f"sudo pacman -S {arch_pkg}")
            except Exception as e:
                print(f"Failed to install Python packages: {e}")
                print("\nPlease install the required packages manually:")
                print("sudo pacman -S python-requests python-beautifulsoup4 python-distro")
                sys.exit(1)
        else:
            pip_cmd = [sys.executable, '-m', 'pip']
            try:
                subprocess.check_call(pip_cmd + ['install', '-r', 'requirements.txt'])
            except subprocess.CalledProcessError:
                print("\nTrying alternative installation method...")
                with open('requirements.txt', 'r') as f:
                    packages = f.read().splitlines()
                    for package in packages:
                        if package.strip() and not package.startswith('#'):
                            try:
                                subprocess.check_call(pip_cmd + ['install', package])
                            except subprocess.CalledProcessError as e:
                                print(f"Failed to install {package}: {e}")
                                print("Please install it manually using:")
                                print(f"python -m pip install {package}")
    except Exception as e:
        print(f"Failed to install Python packages: {e}")
        if os_type == "arch":
            print("\nPlease install the required packages manually:")
            print("sudo pacman -S python-requests python-beautifulsoup4 python-distro")
        else:
            print("\nPlease install the required packages manually:")
            print("python -m pip install -r requirements.txt")
        sys.exit(1)

def create_symlink():
    try:
        current_dir = os.path.abspath(os.path.dirname(__file__))
        script_path = os.path.join(current_dir, 'proxy_anonymizer.py')
        
        os.makedirs('/usr/local/bin', exist_ok=True)
        
        symlink_path = '/usr/local/bin/anonymizer'
        if os.path.exists(symlink_path):
            os.remove(symlink_path)
        os.symlink(script_path, symlink_path)
        
        os.chmod(script_path, 0o755)
        os.chmod(symlink_path, 0o755)
    except Exception as e:
        print(f"Failed to create symlink: {e}")
        sys.exit(1)

def create_config_dir():
    try:
        config_dir = os.path.expanduser('~/.config/proxy-anonymizer')
        os.makedirs(config_dir, exist_ok=True)
        
        shutil.copy('proxy_anonymizer.py', config_dir)
        shutil.copy('requirements.txt', config_dir)
        
        os.chmod(os.path.join(config_dir, 'proxy_anonymizer.py'), 0o755)
    except Exception as e:
        print(f"Failed to create configuration directory: {e}")
        sys.exit(1)

def main():
    print("Starting Proxy Anonymizer installation...")
    
    check_root()
    
    os_type = detect_os()
    print(f"\nDetected OS type: {os_type}")
    if os_type == "unknown":
        print("Warning: Unsupported OS detected. Installation may not work properly.")
        print("Please ensure you have the required dependencies installed manually.")
    
    print("\nInstalling system dependencies...")
    install_dependencies()
    
    print("\nInstalling Python packages...")
    install_python_packages()
    
    print("\nCreating configuration directory...")
    create_config_dir()
    
    print("\nCreating system-wide command...")
    create_symlink()
    
    print("\nInstallation complete!")
    print("\nYou can now run the program by typing 'anonymizer' in your terminal.")
    print("\nConfiguration files are stored in ~/.config/proxy-anonymizer/")
    print("Log files are stored in ~/.proxy_anonymizer.log")

if __name__ == "__main__":
    main() 
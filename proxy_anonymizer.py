#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import os
import subprocess
import sys
import requests
import random
import json
from typing import Optional, Dict, List
import logging
from pathlib import Path
from bs4 import BeautifulSoup
import concurrent.futures
from urllib.parse import urlparse
import socketserver
import http.server
import threading
import socket
import select
import platform
import distro

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('proxy_anonymizer.log'),
        logging.StreamHandler()
    ]
)

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.proxies = kwargs.pop('proxies', None)
        super().__init__(*args, **kwargs)
        # Disable all logging
        self.log_message = lambda *args: None
        self.log_error = lambda *args: None
        self.log_request = lambda *args: None

    def send_error(self, code, message=None):
        """Override send_error to suppress error messages"""
        try:
            self.send_response(code)
            self.send_header('Connection', 'close')
            self.end_headers()
        except Exception:
            pass

    def do_CONNECT(self):
        """Handle CONNECT requests for HTTPS"""
        try:
            # Parse the host and port from the path
            host, port = self.path.split(':')
            port = int(port)

            # Create a socket to the target server through the proxy
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Connect to the proxy first
            proxy_host, proxy_port = self.proxies['http'].split('://')[1].split(':')
            target_socket.connect((proxy_host, int(proxy_port)))
            
            # Send CONNECT request to the proxy
            connect_request = f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n"
            target_socket.send(connect_request.encode())
            
            # Read proxy response
            response = target_socket.recv(4096)
            if not response.startswith(b'HTTP/1.1 200'):
                raise Exception("Proxy connection failed")
            
            # Send 200 Connection established to client
            self.send_response(200, 'Connection established')
            self.send_header('Connection', 'close')
            self.end_headers()

            # Create a tunnel between the client and target
            self.tunnel(target_socket)
        except Exception:
            self.send_error(500)

    def tunnel(self, target_socket):
        """Create a tunnel between client and target"""
        try:
            # Get the client socket
            client_socket = self.connection

            # Set up the tunnel
            while True:
                # Check if client socket is readable
                r, w, x = select.select([client_socket, target_socket], [], [])
                if client_socket in r:
                    data = client_socket.recv(8192)
                    if not data:
                        break
                    target_socket.send(data)
                if target_socket in r:
                    data = target_socket.recv(8192)
                    if not data:
                        break
                    client_socket.send(data)
        except Exception:
            pass
        finally:
            target_socket.close()

    def do_GET(self):
        try:
            # Get the full URL
            url = self.path
            if not url.startswith('http'):
                url = 'http://' + self.headers.get('Host', '') + url

            # Forward the request through the current proxy
            response = requests.get(url, proxies=self.proxies, timeout=10)
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response.content)
        except Exception:
            self.send_error(500)

    def do_POST(self):
        try:
            # Get the full URL
            url = self.path
            if not url.startswith('http'):
                url = 'http://' + self.headers.get('Host', '') + url

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Forward the request through the current proxy
            response = requests.post(url, data=post_data, proxies=self.proxies, timeout=10)
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response.content)
        except Exception:
            self.send_error(500)

    def handle_one_request(self):
        """Handle one request, possibly blocking."""
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(414)
                return
            if not self.raw_requestline:
                self.close_connection = 1
                return
            if not self.parse_request():
                return

            mname = 'do_' + self.command
            if not hasattr(self, mname):
                self.send_error(501)
                return
            method = getattr(self, mname)
            method()
            self.wfile.flush()
        except Exception:
            self.close_connection = 1

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""
    pass

class ProxyAnonymizer:
    def __init__(self):
        self.proxy_list: List[Dict[str, str]] = []
        self.current_proxy: Optional[Dict[str, str]] = None
        self.verify_url = "http://checkip.amazonaws.com"
        self.config_file = Path.home() / ".proxy_anonymizer_config.json"
        self.tor_port = 9050  # Default Tor SOCKS port
        self.tor_control_port = 9051  # Default Tor control port
        self.local_proxy_server = None
        self.os_type = self.detect_os()
        self.load_config()
        self.ensure_tor_running()

    def detect_os(self) -> str:
        try:
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

    def install_dependencies(self) -> None:
        """Install required dependencies"""
        try:
            import requests
            import bs4
        except ImportError:
            if self.os_type == "arch":
                subprocess.check_call('sudo pacman -Sy --noconfirm python-requests python-beautifulsoup4', shell=True)
            elif self.os_type == "debian":
                subprocess.check_call('sudo apt update && sudo apt install -y python3-requests python3-bs4', shell=True)
            elif self.os_type == "rhel":
                subprocess.check_call('sudo dnf install -y python3-requests python3-beautifulsoup4', shell=True)
            else:
                print("Unsupported OS. Please install dependencies manually.")
                sys.exit(1)

    def install_tor(self) -> None:
        """Install and configure Tor"""
        try:
            subprocess.check_output('which tor', shell=True)
        except subprocess.CalledProcessError:
            if self.os_type == "arch":
                subprocess.check_call('sudo pacman -Sy --noconfirm tor', shell=True)
            elif self.os_type == "debian":
                subprocess.check_call('sudo apt update && sudo apt install -y tor', shell=True)
            elif self.os_type == "rhel":
                subprocess.check_call('sudo dnf install -y tor', shell=True)
            else:
                print("Unsupported OS. Please install Tor manually.")
                sys.exit(1)
            self.start_tor_service()

    def start_tor_service(self) -> None:
        if self.os_type in ["arch", "debian", "rhel"]:
            subprocess.check_call('sudo systemctl start tor', shell=True)
            time.sleep(2)

    def ensure_tor_running(self) -> None:
        """Ensure Tor service is running"""
        try:
            # Check if Tor is running
            subprocess.check_output('systemctl is-active tor', shell=True)
        except subprocess.CalledProcessError:
            self.start_tor_service()

    def get_tor_ip(self) -> str:
        """Get current IP through Tor network"""
        try:
            proxies = {
                'http': f'socks5://127.0.0.1:{self.tor_port}',
                'https': f'socks5://127.0.0.1:{self.tor_port}'
            }
            response = requests.get(self.verify_url, proxies=proxies, timeout=10)
            return response.text.strip()
        except requests.RequestException as e:
            logging.error(f"Failed to get Tor IP: {e}")
            return "Unknown"

    def new_tor_circuit(self) -> None:
        """Request new Tor circuit"""
        try:
            # Send signal to Tor to get new circuit
            subprocess.check_call(f'echo -e "AUTHENTICATE\r\nSIGNAL NEWNYM\r\nQUIT" | nc localhost {self.tor_control_port}', shell=True)
            time.sleep(2)  # Wait for new circuit to be established
            logging.info("New Tor circuit established")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to get new Tor circuit: {e}")
            # Try alternative method using systemctl
            try:
                subprocess.check_call('sudo systemctl restart tor', shell=True)
                time.sleep(2)
                logging.info("Tor service restarted for new circuit")
            except subprocess.CalledProcessError:
                logging.error("Failed to restart Tor service")

    def verify_proxy(self, proxy: Dict[str, str]) -> bool:
        """Verify if a proxy is working"""
        try:
            proxies = {
                "http": f"{proxy['type']}://{proxy['host']}:{proxy['port']}",
                "https": f"{proxy['type']}://{proxy['host']}:{proxy['port']}"
            }
            # Try multiple times with different timeouts
            for _ in range(3):
                try:
                    response = requests.get(self.verify_url, proxies=proxies, timeout=10)
                    if response.status_code == 200:
                        return True
                except requests.RequestException:
                    time.sleep(1)  # Wait before retry
            return False
        except Exception:
            return False

    def add_proxy(self, proxy_type: str, host: str, port: str) -> None:
        """Add a new proxy to the list"""
        proxy = {
            "type": proxy_type,
            "host": host,
            "port": port
        }
        if self.verify_proxy(proxy):
            self.proxy_list.append(proxy)
            self.save_config()
            logging.info(f"Added new proxy: {host}:{port}")
        else:
            logging.error(f"Failed to verify proxy: {host}:{port}")

    def change_proxy(self) -> None:
        """Change to a random proxy from the list"""
        clear_screen()
        self.print_banner()
        
        if not self.proxy_list:
            print("\033[1;31mNo proxies available. Please update the proxy list first.\033[0m")
            return

        self.current_proxy = random.choice(self.proxy_list)
        proxies = {
            "http": f"{self.current_proxy['type']}://{self.current_proxy['host']}:{self.current_proxy['port']}",
            "https": f"{self.current_proxy['type']}://{self.current_proxy['host']}:{self.current_proxy['port']}"
        }
        
        try:
            response = requests.get(self.verify_url, proxies=proxies, timeout=10)
            new_ip = response.text.strip()
            print(f"\n\033[1;32mSuccessfully changed IP to: {new_ip}\033[0m")
            print(f"Using proxy: {self.current_proxy['type']}://{self.current_proxy['host']}:{self.current_proxy['port']}")
        except requests.RequestException as e:
            print(f"\n\033[1;31mFailed to change proxy: {e}\033[0m")

    def save_config(self) -> None:
        """Save proxy configuration to file"""
        config = {
            "proxy_list": self.proxy_list,
            "current_proxy": self.current_proxy
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)

    def load_config(self) -> None:
        """Load proxy configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.proxy_list = config.get("proxy_list", [])
                    self.current_proxy = config.get("current_proxy")
            except json.JSONDecodeError:
                logging.error("Failed to load configuration file")

    def print_banner(self) -> None:
        """Print program banner"""
        clear_screen()
        banner = """
        \033[1;32m
        ╔══════════════════════════════════════════════════════════╗
        ║                 Proxy Anonymizer v1.0                    ║
        ║                                                          ║
        ║  A modern proxy management and IP anonymization tool     ║
        ╚══════════════════════════════════════════════════════════╝
        \033[0m
        """
        print(banner)

    def print_menu(self) -> None:
        """Print the main menu"""
        print("\n\033[1;36mOptions:\033[0m")
        print("\033[1;33m1\033[0m. Change proxy")
        print("\033[1;33m2\033[0m. List available proxies")
        print("\033[1;33m3\033[0m. Update free proxies")
        print("\033[1;33m4\033[0m. Start proxy rotation")
        print("\033[1;33m5\033[0m. Exit")

    def print_proxy_list(self) -> None:
        """Print the list of available proxies"""
        clear_screen()
        self.print_banner()
        print("\n\033[1;36mAvailable Proxies:\033[0m")
        if not self.proxy_list:
            print("\033[1;31mNo proxies available. Please update the proxy list first.\033[0m")
            return
        
        for i, proxy in enumerate(self.proxy_list, 1):
            status = "\033[1;32m✓\033[0m" if proxy == self.current_proxy else " "
            print(f"{status} {i}. {proxy['type']}://{proxy['host']}:{proxy['port']}")

    def fetch_free_proxies(self) -> List[Dict[str, str]]:
        """Fetch free proxies from various sources"""
        proxies = []
        sources = [
            "https://free-proxy-list.net/",
            "https://www.sslproxies.org/",
            "https://www.us-proxy.org/"
        ]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        for source in sources:
            try:
                response = requests.get(source, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table')
                
                if table:
                    for row in table.find_all('tr')[1:]:  # Skip header row
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            ip = cols[0].text.strip()
                            port = cols[1].text.strip()
                            proxy_type = 'https' if 'sslproxies' in source else 'http'
                            
                            proxy = {
                                'type': proxy_type,
                                'host': ip,
                                'port': port
                            }
                            proxies.append(proxy)
            except Exception as e:
                logging.error(f"Failed to fetch proxies from {source}: {e}")

        return proxies

    def update_free_proxies(self) -> None:
        """Update the proxy list with fresh free proxies"""
        clear_screen()
        self.print_banner()
        print("\n\033[1;36mUpdating free proxies...\033[0m")
        
        try:
            # Get desired number of proxies
            while True:
                try:
                    desired_quantity = input("\nEnter the number of working proxies you want (default: 100): ").strip()
                    if not desired_quantity:
                        desired_quantity = 100
                    else:
                        desired_quantity = int(desired_quantity)
                    if desired_quantity > 0:
                        break
                    print("\033[1;31mPlease enter a positive number.\033[0m")
                except ValueError:
                    print("\033[1;31mPlease enter a valid number.\033[0m")
            
            logging.info("Fetching free proxies...")
            new_proxies = self.fetch_free_proxies()
            print(f"\nFound {len(new_proxies)} potential proxies")
            
            print(f"\nVerifying proxies until finding {desired_quantity} working ones (this may take a few minutes)...")
            print("Press Ctrl+C to stop and return to menu")
            
            working_proxies = self.verify_proxies_concurrently(new_proxies, desired_quantity)
            
            # Add only new working proxies to the list
            existing_proxies = {(p['host'], p['port']) for p in self.proxy_list}
            for proxy in working_proxies:
                if (proxy['host'], proxy['port']) not in existing_proxies:
                    self.proxy_list.append(proxy)
            
            self.save_config()
            print(f"\n\033[1;32mAdded {len(working_proxies)} new working proxies\033[0m")
            print("\nPress Enter to return to menu...")
            input()
            
        except KeyboardInterrupt:
            print("\n\n\033[1;33mProxy update interrupted. Returning to menu...\033[0m")
            time.sleep(1)
            return

    def verify_proxies_concurrently(self, proxies: List[Dict[str, str]], desired_quantity: int = 100, max_workers: int = 20) -> List[Dict[str, str]]:
        """Verify multiple proxies concurrently"""
        working_proxies = []
        timeout_seconds = 300  # 5 minutes timeout
        
        def verify_single_proxy(proxy: Dict[str, str]) -> Optional[Dict[str, str]]:
            if self.verify_proxy(proxy):
                return proxy
            return None

        logging.info(f"Verifying proxies until finding {desired_quantity} working ones or checking all available proxies...")
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_proxy = {executor.submit(verify_single_proxy, proxy): proxy for proxy in proxies}
                
                try:
                    for future in concurrent.futures.as_completed(future_to_proxy, timeout=timeout_seconds):
                        result = future.result()
                        if result:
                            working_proxies.append(result)
                            print(f"\r\033[1;32mWorking proxies found: {len(working_proxies)}/{desired_quantity}\033[0m", end="")
                            if len(working_proxies) >= desired_quantity:
                                print("\n\033[1;32mReached desired number of proxies!\033[0m")
                                break
                except concurrent.futures.TimeoutError:
                    print(f"\n\033[1;33mProxy verification timed out after {timeout_seconds} seconds\033[0m")
                except Exception as e:
                    print(f"\n\033[1;31mError during proxy verification: {e}\033[0m")
                
        except KeyboardInterrupt:
            print("\n\033[1;33mProxy verification interrupted by user\033[0m")
            return working_proxies

        return working_proxies

    def configure_firefox_proxy(self, port: int) -> None:
        """Configure Firefox to use the local proxy"""
        try:
            # Create Firefox profile directory if it doesn't exist
            firefox_profile = os.path.expanduser("~/.mozilla/firefox/proxy_rotation")
            if not os.path.exists(firefox_profile):
                os.makedirs(firefox_profile)

            # Create user.js with proxy settings
            user_js = os.path.join(firefox_profile, "user.js")
            proxy_settings = f"""
// Proxy settings
user_pref("network.proxy.type", 1);
user_pref("network.proxy.http", "127.0.0.1");
user_pref("network.proxy.http_port", {port});
user_pref("network.proxy.ssl", "127.0.0.1");
user_pref("network.proxy.ssl_port", {port});
user_pref("network.proxy.socks", "127.0.0.1");
user_pref("network.proxy.socks_port", {port});
user_pref("network.proxy.socks_version", 5);
user_pref("network.proxy.socks_remote_dns", true);
user_pref("network.proxy.no_proxies_on", "");
            """
            with open(user_js, "w") as f:
                f.write(proxy_settings)

            return firefox_profile
        except Exception as e:
            logging.error(f"Failed to configure Firefox proxy: {e}")
            return None

    def start_firefox_with_proxy(self, profile_path: str) -> None:
        """Start Firefox with the configured proxy profile"""
        try:
            subprocess.Popen(["firefox", "-P", "proxy_rotation", "-no-remote"])
            logging.info("Firefox started with proxy settings")
        except Exception as e:
            logging.error(f"Failed to start Firefox: {e}")

    def start_local_proxy_server(self, port: int) -> None:
        """Start a local proxy server that forwards requests through the current proxy"""
        def run_server():
            try:
                handler = lambda *args, **kwargs: ProxyHandler(*args, proxies=self.get_current_proxies(), **kwargs)
                self.local_proxy_server = ThreadedHTTPServer(('127.0.0.1', port), handler)
                self.local_proxy_server.serve_forever()
            except Exception as e:
                logging.error(f"Local proxy server error: {e}")

        # Start the server in a separate thread
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        logging.info(f"Local proxy server started on port {port}")

    def stop_local_proxy_server(self) -> None:
        """Stop the local proxy server"""
        if self.local_proxy_server:
            self.local_proxy_server.shutdown()
            self.local_proxy_server.server_close()
            logging.info("Local proxy server stopped")

    def get_current_proxies(self) -> Dict[str, str]:
        """Get the current proxy configuration"""
        if self.current_proxy:
            return {
                "http": f"{self.current_proxy['type']}://{self.current_proxy['host']}:{self.current_proxy['port']}",
                "https": f"{self.current_proxy['type']}://{self.current_proxy['host']}:{self.current_proxy['port']}"
            }
        else:
            return {
                'http': f'socks5://127.0.0.1:{self.tor_port}',
                'https': f'socks5://127.0.0.1:{self.tor_port}'
            }

    def start_proxy_rotation(self) -> None:
        """Start automatic proxy rotation"""
        clear_screen()
        self.print_banner()
        
        if not self.proxy_list:
            print("\033[1;31mNo proxies available. Please update the proxy list first.\033[0m")
            print("\nPress Enter to return to menu...")
            input()
            return

        try:
            # Get rotation delay
            while True:
                try:
                    delay_input = input("\nEnter rotation delay in seconds (minimum 30, 0 or Enter for infinite): ").strip()
                    if not delay_input:
                        delay = 0
                    else:
                        delay = int(delay_input)
                        if delay > 0 and delay < 30:
                            print("\033[1;33mDelay set to minimum of 30 seconds to prevent connection issues\033[0m")
                            delay = 30
                    if delay >= 0:
                        break
                except ValueError:
                    print("\033[1;31mPlease enter a valid number.\033[0m")

            # Get local proxy port
            while True:
                try:
                    local_port = input("\nEnter local proxy port (default: 5005): ").strip()
                    if not local_port:
                        local_port = 5005
                    else:
                        local_port = int(local_port)
                    if 1024 <= local_port <= 65535:
                        break
                    print("\033[1;31mPlease enter a port number between 1024 and 65535.\033[0m")
                except ValueError:
                    print("\033[1;31mPlease enter a valid port number.\033[0m")

            print("\n\033[1;36mProxy Rotation Settings:\033[0m")
            print(f"Rotation delay: {'Infinite (30s minimum)' if delay == 0 else f'{delay} seconds'}")
            print(f"Local proxy port: {local_port}")

            # Start local proxy server
            print("\n\033[1;33mStarting local proxy server...\033[0m")
            self.start_local_proxy_server(local_port)
            time.sleep(2)  # Wait for server to start

            # Configure and start Firefox
            print("\n\033[1;33mConfiguring Firefox proxy settings...\033[0m")
            profile_path = self.configure_firefox_proxy(local_port)
            if profile_path:
                print("\033[1;32mFirefox proxy settings configured successfully\033[0m")
                print("\nPress Enter to start Firefox and begin rotation (Ctrl+C to stop)...")
                input()
                self.start_firefox_with_proxy(profile_path)
            else:
                print("\033[1;31mFailed to configure Firefox. Please configure your browser manually.\033[0m")
                print("\n\033[1;33mPlease configure your browser to use:\033[0m")
                print(f"HTTP Proxy: 127.0.0.1:{local_port}")
                print(f"SOCKS Proxy: 127.0.0.1:{local_port}")
                print("\nPress Enter to start rotation (Ctrl+C to stop)...")
                input()

            print("\n\033[1;32mStarting proxy rotation...\033[0m")
            print("Press Ctrl+C to stop")
            
            rotation_running = True
            while rotation_running:
                try:
                    # Try to use a random proxy first
                    self.current_proxy = random.choice(self.proxy_list)
                    proxies = self.get_current_proxies()
                    
                    try:
                        # Try to get IP through proxy
                        response = requests.get(self.verify_url, proxies=proxies, timeout=10)
                        new_ip = response.text.strip()
                        proxy_type = "External Proxy"
                    except requests.RequestException:
                        # If proxy fails, use Tor
                        self.new_tor_circuit()
                        new_ip = self.get_tor_ip()
                        proxy_type = "Tor Network"
                        proxies = {
                            'http': f'socks5://127.0.0.1:{self.tor_port}',
                            'https': f'socks5://127.0.0.1:{self.tor_port}'
                        }
                    
                    # Display current status
                    clear_screen()
                    self.print_banner()
                    print("\n\033[1;36mCurrent Proxy Status:\033[0m")
                    print(f"IP Address: {new_ip}")
                    print(f"Connection Type: {proxy_type}")
                    if proxy_type == "External Proxy":
                        print(f"Proxy: {self.current_proxy['type']}://{self.current_proxy['host']}:{self.current_proxy['port']}")
                    else:
                        print(f"Tor SOCKS Port: {self.tor_port}")
                    if delay > 0:
                        print(f"Next rotation in: {delay} seconds")
                    else:
                        print("Rotation mode: Infinite (30s minimum)")
                    print("\n\033[1;33mPress Ctrl+C to stop\033[0m")
                    
                    if delay > 0:
                        # Wait for next rotation with countdown
                        for i in range(delay, 0, -1):
                            print(f"\rTime until next rotation: {i} seconds", end="")
                            time.sleep(1)
                        print()
                    else:
                        # Infinite rotation with minimum 30-second delay
                        for i in range(30, 0, -1):
                            print(f"\rTime until next rotation: {i} seconds", end="")
                            time.sleep(1)
                        print()
                    
                except KeyboardInterrupt:
                    print("\n\n\033[1;33mProxy rotation stopped by user\033[0m")
                    rotation_running = False
                except Exception as e:
                    print(f"\n\033[1;31mError during proxy rotation: {e}\033[0m")
                    print("Waiting 30 seconds before retrying...")
                    for i in range(30, 0, -1):
                        print(f"\rRetrying in: {i} seconds", end="")
                        time.sleep(1)
                    print()
            
            # Stop the local proxy server when rotation ends
            self.stop_local_proxy_server()
                    
        except KeyboardInterrupt:
            print("\n\n\033[1;33mProxy rotation setup cancelled\033[0m")
            self.stop_local_proxy_server()
            time.sleep(1)
            return

def main():
    anonymizer = ProxyAnonymizer()
    anonymizer.install_dependencies()
    anonymizer.install_tor()
    
    try:
        while True:
            anonymizer.print_banner()
            print("\n\033[1;36mOptions:\033[0m")
            print("\033[1;33m1\033[0m. Change proxy")
            print("\033[1;33m2\033[0m. List available proxies")
            print("\033[1;33m3\033[0m. Update free proxies")
            print("\033[1;33m4\033[0m. Start proxy rotation")
            print("\033[1;33m5\033[0m. Exit")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                anonymizer.change_proxy()
                print("\nPress Enter to return to menu...")
                input()
            
            elif choice == "2":
                anonymizer.print_proxy_list()
                print("\nPress Enter to return to menu...")
                input()
            
            elif choice == "3":
                anonymizer.update_free_proxies()
            
            elif choice == "4":
                anonymizer.start_proxy_rotation()
            
            elif choice == "5":
                print("\nExiting...")
                break
            
            else:
                print("\n\033[1;31mInvalid choice. Please try again.\033[0m")
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n\n\033[1;33mProgram interrupted by user. Exiting...\033[0m")
        sys.exit(0)

if __name__ == "__main__":
    main() 
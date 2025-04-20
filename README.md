# Proxy Anonymizer v1.2

A modern proxy management and IP anonymization tool that helps you maintain privacy while browsing the internet. This tool allows you to rotate through multiple proxies, including Tor, to keep your IP address anonymous.

## Changelog

### v1.2
- Added system-wide installation script
- Improved installation process
- Removed SSL/TLS encryption for better compatibility
- Added automatic dependency installation
- Added configuration directory in ~/.config/proxy-anonymizer/

### v1.1
- Added proxy list cleanup feature
- Added netcat requirement check
- Improved proxy verification
- Added automatic netcat installation

### v1.0
- Initial release
- Basic proxy management
- Tor integration
- Firefox configuration
- Proxy rotation

## Features

- **Proxy Management**: Add, verify, and manage multiple proxies
- **Automatic Proxy Rotation**: Rotate through proxies at configurable intervals
- **Tor Integration**: Seamless integration with Tor network as a fallback
- **Firefox Integration**: Automatic configuration of Firefox proxy settings
- **Proxy Scraping**: Automatically fetch and verify proxies from multiple sources
- **Proxy List Maintenance**: Clean up and verify existing proxy list
- **Cross-Platform**: Works on Linux distributions (Debian, Arch, RHEL-based)
- **Local Proxy Server**: Built-in local proxy server for easy browser configuration

## Requirements

- Python 3.x
- Linux-based operating system (Debian, Arch, or RHEL-based)
- Firefox browser (optional, for automatic proxy configuration)
- Tor (optional, for Tor network integration)
- netcat (nc) - Required for some features

## Installation

### Quick Installation

1. Clone the repository:
```bash
git clone https://github.com/Th3drata/proxy-anonymizer.git
cd proxy-anonymizer
```

2. Run the installation script:
```bash
sudo python3 install.py
```

This will:
- Install all required dependencies
- Create a system-wide command `anonymizer`
- Set up configuration files in `~/.config/proxy-anonymizer/`
- Create log files in `~/.proxy_anonymizer.log`

3. Run the program:
```bash
anonymizer
```

### Manual Installation

If you prefer to install manually:

1. Clone the repository:
```bash
git clone https://github.com/Th3drata/proxy-anonymizer.git
cd proxy-anonymizer
```

2. Make the script executable:
```bash
chmod +x proxy_anonymizer.py
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

4. Run the script:
```bash
./proxy_anonymizer.py
```

The script will automatically:
- Install required Python dependencies
- Install and configure Tor (if not already installed)
- Install netcat if not present
- Create necessary configuration files
- Check for required system tools

### Arch Linux Installation

For Arch Linux users, you can install the requirements using pacman:

1. Install system dependencies:
```bash
sudo pacman -S python python-pip tor gnu-netcat
```

2. Install Python packages:
```bash
pip install -r requirements.txt
```

3. Make the script executable:
```bash
chmod +x proxy_anonymizer.py
```

4. Start Tor service:
```bash
sudo systemctl start tor
sudo systemctl enable tor  # Optional: enable Tor to start on boot
```

5. Run the script:
```bash
./proxy_anonymizer.py
```

## Usage

The program provides a simple menu-driven interface with the following options:

1. **Change proxy**: Manually switch to a different proxy
2. **List available proxies**: View all configured proxies
3. **Update proxies**: Fetch and verify new proxies
4. **Clean up proxy list**: Remove non-working proxies from the list
5. **Start proxy rotation**: Begin automatic proxy rotation
6. **Exit**: Close the program

### Proxy Rotation

When starting proxy rotation, you can configure:
- Rotation delay (minimum 30 seconds)
- Local proxy port (default: 5005)
- Automatic Firefox configuration

The rotation will:
1. Try to use a random proxy from your list
2. Fall back to Tor if the proxy fails
3. Display current IP address and connection type
4. Automatically rotate at the specified interval

## Configuration

The program stores its configuration in:
- `~/.proxy_anonymizer_config.json`: Proxy list and current proxy settings
- `~/.mozilla/firefox/proxy_rotation/`: Firefox proxy profile (if used)

## Security Notes

- The program uses public proxies, which may not be secure or reliable
- Always verify the security of any proxy before using it
- Consider using Tor for maximum anonymity
- For maximum security, use trusted proxy servers

## Troubleshooting

- If Firefox configuration fails, you can manually configure your browser to use:
  - HTTP Proxy: 127.0.0.1:[local_port]
  - SOCKS Proxy: 127.0.0.1:[local_port]
- Check the `proxy_anonymizer.log` file for detailed error messages
- Ensure Tor is running if you want to use it as a fallback

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) license. This means you are free to:

- Share — copy and redistribute the material in any medium or format
- Adapt — remix, transform, and build upon the material

Under the following terms:

- Attribution — You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.
- NonCommercial — You may not use the material for commercial purposes.

For more information, see the [LICENSE](LICENSE) file.

## About

This project is maintained by [Th3drata](https://github.com/Th3drata). Feel free to contribute by opening issues or submitting pull requests.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 
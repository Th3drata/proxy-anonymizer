# Proxy Anonymizer

A modern proxy management and IP anonymization tool that helps you maintain privacy and security while browsing the internet. This tool allows you to rotate through multiple proxies, including Tor, to keep your IP address anonymous.

## Features

- **Proxy Management**: Add, verify, and manage multiple proxies
- **Automatic Proxy Rotation**: Rotate through proxies at configurable intervals
- **Tor Integration**: Seamless integration with Tor network as a fallback
- **Firefox Integration**: Automatic configuration of Firefox proxy settings
- **Free Proxy Scraping**: Automatically fetch and verify free proxies from multiple sources
- **Cross-Platform**: Works on Linux distributions (Debian, Arch, RHEL-based)
- **Local Proxy Server**: Built-in local proxy server for easy browser configuration

## Requirements

- Python 3.x
- Linux-based operating system (Debian, Arch, or RHEL-based)
- Firefox browser (optional, for automatic proxy configuration)
- Tor (optional, for Tor network integration)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd proxy-anonymizer
```

2. Make the script executable:
```bash
chmod +x proxy_anonymizer.py
```

3. Run the script:
```bash
./proxy_anonymizer.py
```

The script will automatically:
- Install required Python dependencies
- Install and configure Tor (if not already installed)
- Create necessary configuration files

## Usage

The program provides a simple menu-driven interface with the following options:

1. **Change proxy**: Manually switch to a different proxy
2. **List available proxies**: View all configured proxies
3. **Update free proxies**: Fetch and verify new free proxies
4. **Start proxy rotation**: Begin automatic proxy rotation
5. **Exit**: Close the program

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

- The program uses free proxies, which may not be secure or reliable
- Always verify the security of any proxy before using it
- Consider using Tor for maximum anonymity
- The program does not encrypt your traffic - use HTTPS for secure connections

## Troubleshooting

- If Firefox configuration fails, you can manually configure your browser to use:
  - HTTP Proxy: 127.0.0.1:[local_port]
  - SOCKS Proxy: 127.0.0.1:[local_port]
- Check the `proxy_anonymizer.log` file for detailed error messages
- Ensure Tor is running if you want to use it as a fallback

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here] 
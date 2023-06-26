#!/usr/bin/env python3
import argparse
import os
from socket import IPPROTO_IP, IP_TOS
import time
import urllib3

# The DS (formally the TOS byte) in the TCP header is used
# to indicate to routers the priority of the traffic.
# There is a table in https://tucny.com/Home/dscp-tos
# Also https://linuxreviews.org/Type_of_Service_(ToS)_and_DSCP_Values
# shows how to set it in linux using "iptables -j DSCP"
# Sensible values are
# 0 Default best efforts
# 8 Maximize throughput, e.g. FTP or SMB
# 16 Minimize delay, e.g. SSH or Ping
# 40 Priority throughput.

# wayback machine link in case linuxreviews not available
# https://web.archive.org/web/20230622154204/https://linuxreviews.org/Type_of_Service_(ToS)_and_DSCP_Values

# Download a URL, optionally setting custom TOS byte.
# Output filename can be given.
# Chatty, as we want to see what is happening
def download_with_speed(url, custom_tos=None, output=None):
    start_time = time.time()
    downloaded_bytes = 0
    displayed_time = 0
    content_length = ''
    percent = ' ??%'
    size = 0

    # Create a custom urllib3 PoolManager.
    # Needed to set the tos.
    manager = urllib3.PoolManager()

    # Set the custom TOS value if provided
    if custom_tos is not None:
        manager.connection_pool_kw['socket_options'] = [(IPPROTO_IP, IP_TOS, custom_tos)]

    # Make the request
    with manager.request('GET', url, preload_content=False) as response:
        # Extract the filename from the URL if not specified
        filename = output or os.path.basename(url)
        if 'Content-Length' in response.headers:
            content_length = "/"+response.headers['Content-Length']
            size=int(response.headers['Content-Length'])

        # Open a file for writing
        with open(filename, 'wb') as file:
            for chunk in response.stream(1024):
                downloaded_bytes += len(chunk)
                elapsed_time = time.time() - start_time
                if elapsed_time >= displayed_time:
                    # Print status message
                    if size > 0:
                        percent = downloaded_bytes / size *100
                        percent = f"{percent:3.0f}%"
                    download_speed = downloaded_bytes / elapsed_time
                    print(f"Downloaded: {downloaded_bytes}{content_length} bytes {percent}| Speed: {download_speed:9.2f} bytes/sec", end='\r')
                    displayed_time = elapsed_time+0.5

                # Write the chunk to the file
                file.write(chunk)
        # file should be closed here. Should handle out of disk errors.

    # Print final status message
    elapsed_time = time.time() - start_time
    download_speed = downloaded_bytes / elapsed_time
    print(f"\nDownloaded: {downloaded_bytes} bytes in {elapsed_time:.2f} seconds| Speed: {download_speed:.2f} bytes/sec")
    print(f"File saved as: {filename}")

# main function. Should pass in sys.argv
def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Python program to download a file with custom TOS')
    parser.add_argument('-o', '--output', type=str, default=None, help='output filename')
    parser.add_argument('-t', '--tos', type=int, default=None, help='''Type of Service (TOS) value    0 Default, 8 FTP, 16 SSH Ping''')
    parser.add_argument('url', type=str, help='URL to download the file')
    args = parser.parse_args()

    # Download the file with speed and custom TOS setting
    download_with_speed(args.url, args.tos, args.output)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
""" Use psutil to query system information """

import os
import sys
import time
import socket
import json
import psutil
import platform
import flask
import conf

from datetime import datetime

class SystemData:

    def __init__(self):
        self.sysinfo = ""
        self.ipaddr = ""
        self.uptime = ""

    def get_local_ip(self):
        ''' Create Socket to the Internet, Query Local IP '''
        ipaddr = "UNKN"
        try:
            # connect to the host -- tells us if the host is actually
            # reachable
            sock = socket.create_connection(("ipv4.google.com", 80))
            if sock is not None:
                ipaddr = sock.getsockname()[0]
                print('Closing socket')
                sock.close()
            return ipaddr
        except OSError:
            pass
        return "0.0.0.0"

    def local_ip(self):
        return self.ipaddr

    def refresh(self):
        self.sysinfo = self.query_system_information()
        self.ipaddr = self.get_local_ip()
        self.uptime = "UNK"

    def get_size(self, bytes, suffix="B"):
        """
        Scale bytes to its proper format
        e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
        """
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes < factor:
                return f"{bytes:.2f}{unit}{suffix}"
            bytes /= factor

    def query_system_information(self):
        """ Generate useful system description """
        uname = platform.uname()
        # Get system information
        sysinfo_text = "="*20 + "System Information" + "="*20 + "<br> \n"
        sysinfo_text += f"System: {uname.system}" + "<br> \n"
        sysinfo_text += f"Node Name: {uname.node}" + "<br> \n"
        sysinfo_text += f"Release: {uname.release}" + "<br> \n"
        sysinfo_text += f"Version: {uname.version}" + "<br> \n"
        sysinfo_text += f"Machine: {uname.machine}" + "<br> \n"
        # Software Information
        sysinfo_text += "="*20 + "Software Info" + "="*20 + "<br> \n"
        sysinfo_text += f"Python Version: {sys.version}" + "<br> \n"
        sysinfo_text += f"Flask Version : {flask.__version__}" + "<br> \n"
        # Get CPU information
        sysinfo_text += "="*20 + "CPU Info" + "="*20 + "<br> \n"
        sysinfo_text += f"Physical cores: {psutil.cpu_count(logical=False)}" + "<br> \n"
        sysinfo_text += f"Total cores: {psutil.cpu_count(logical=True)}" + "<br> \n"
        # CPU Frequencies
        cpufreq = psutil.cpu_freq()
        sysinfo_text += f"Max Frequency: {cpufreq.max:.2f}Mhz" + "<br> \n"
        sysinfo_text += f"Min Frequency: {cpufreq.min:.2f}Mhz" + "<br> \n"
        sysinfo_text += f"Current Frequency: {cpufreq.current:.2f}Mhz" + "<br> \n"
        # CPU usage
        sysinfo_text += f"Total CPU Usage: {psutil.cpu_percent()}%" + "<br> \n"
        # Memory Information
        sysinfo_text += "="*20 + "Memory Information" + "="*20 + "<br> \n"
        svmem = psutil.virtual_memory()
        sysinfo_text += f"Total: {self.get_size(svmem.total)}" + "<br> \n"
        sysinfo_text += f"Available: {self.get_size(svmem.available)}" + "<br> \n"
        sysinfo_text += f"Used: {self.get_size(svmem.used)}" + "<br> \n"
        sysinfo_text += f"Percentage: {svmem.percent}%" + "<br> \n"
        sysinfo_text += "="*10 + "SWAP" + "="*10 + "<br> \n"
        # SWAP memory details
        swap = psutil.swap_memory()
        sysinfo_text += f"Total: {self.get_size(swap.total)}" + "<br> \n"
        sysinfo_text += f"Free: {self.get_size(swap.free)}" + "<br> \n"
        sysinfo_text += f"Used: {self.get_size(swap.used)}" + "<br> \n"
        sysinfo_text += f"Percentage: {swap.percent}%" + "<br> \n"
        sysinfo_text += "="*20 + "Disk Information" + "="*20 + "<br> \n"
        sysinfo_text += "Partitions and Usage:" + "<br> \n"
        # get all disk partitions
        partitions = psutil.disk_partitions()
        for partition in partitions:
            sysinfo_text += f"=== Device: {partition.device} ===" + "<br> \n"
            sysinfo_text += f"  Mountpoint: {partition.mountpoint}" + "<br> \n"
            sysinfo_text += f"  File system type: {partition.fstype}" + "<br> \n"
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                # this can be catched due to the disk that
                # isn't ready
                continue
            sysinfo_text += f"  Total Size: {self.get_size(partition_usage.total)}" + "<br> \n"
            sysinfo_text += f"  Used: {self.get_size(partition_usage.used)}" + "<br> \n"
            sysinfo_text += f"  Free: {self.get_size(partition_usage.free)}" + "<br> \n"
            sysinfo_text += f"  Percentage: {partition_usage.percent}%" + "<br> \n"
        # get IO statistics since boot
        disk_io = psutil.disk_io_counters()
        sysinfo_text += f"Total read: {self.get_size(disk_io.read_bytes)}" + "<br> \n"
        sysinfo_text += f"Total write: {self.get_size(disk_io.write_bytes)}" + "<br> \n"

        # Network information
        sysinfo_text += "="*20 + "IPv4 Network Information" + "="*20 + "<br> \n"
        # get all network interfaces (virtual and physical)
        if_addrs = psutil.net_if_addrs()
        for interface_name, interface_addresses in if_addrs.items():
            for address in interface_addresses:
                if str(address.family) == 'AddressFamily.AF_INET':
                    sysinfo_text += f"=== Interface: {interface_name} ({address.family}) ===" + "<br> \n"
                    sysinfo_text += f"  IP Address: {address.address}" + "<br> \n"
                    sysinfo_text += f"  Netmask: {address.netmask}" + "<br> \n"
        # get IO statistics since boot
        net_io = psutil.net_io_counters()
        sysinfo_text += f"Total Bytes Sent: {self.get_size(net_io.bytes_sent)}" + "<br> \n"
        sysinfo_text += f"Total Bytes Received: {self.get_size(net_io.bytes_recv)}" + "<br> \n"
        return sysinfo_text


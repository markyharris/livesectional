# Original scan-network.py by omiq from https://gist.github.com/omiq/2f3edf2624a72e89ba3a3a009a673a21
# and https://makerhacks.com/detect-and-list-raspberry-pi-and-other-boards-on-your-network/
# Altered by Mark Harris for LiveSectional
# Must install nmap; apt-get install nmap
# Must install python-nmap; sudo pip3 install python-nmap

import nmap
import socket

def scan_network():
    machines = []
#    print("One Moment - Scanning Local Network for Other LiveSectional Maps")

    # routine from https://www.w3resource.com/python-exercises/python-basic-exercise-55.php
    loc_ip = ([l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]
              if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)),
              s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET,
              socket.SOCK_DGRAM)]][0][1]]) if l][0][0])

    machines.append(loc_ip + " - " + socket.gethostname() + ": Current")
    pre_ip = loc_ip.rpartition('.')

    nm = nmap.PortScanner()
    nm.scan(pre_ip[0] + '.0/24', '22') # Scan network for port 22 (ssh)

    # iterate over the hosts on the network
    for host in sorted(nm.all_hosts()):
        if len(nm[host]['vendor']) > 0:
            vendor = tuple(nm[host]['vendor'].values())
            if str(vendor).find('Raspberry') > 0 and nm[host].hostname().startswith("lives"): # livesectional hostname?
                h1,h2 = nm[host].hostname().split(".")
                machines.append(host + " - " + h1)

    return(machines)

if __name__ == "__main__":
    print("One Moment - Scanning Local Network for Other LiveSectional Maps")
    machines = scan_network()
    for machine in machines:
        print(machine)

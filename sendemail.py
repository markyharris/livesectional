#!/usr/bin/python

import smtpd
import smtplib

oldip = "192.168.86.33"
newip = "192.168.86.55"
recip = "markyharris@gmail.com"
message = "The IP address on your LiveSectional Map's Raspberry PI has changed.\n The old IP = " + oldip + ".\n " \
          "The new IP address = " + newip + "."

#server = CustomSMTPServer(('127.0.0.1', 1025), None)

#server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
server = smtplib.SMTP('localhost', 1025)
#server.login("livesectionalv4@gmail.com", "livesectional")
server.sendmail(
    "ls@livesectional.com",
    recip,
    message)

server.quit()

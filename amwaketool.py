#!/usr/bin/python2

# Copyright (C) 2016 Adam Makepeace
# Email: adam.makepeace@hotmail.co.uk
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

errlist = list()
import socket
import os
import struct
import sys
import json
import pwd
import subprocess
# import systemd.journal
try: import dbus
except ImportError: errlist.append('dbus')
try: import dbus.mainloop.glib
except ImportError: errlist.append('dbus.mainloop.glib (dbus submodule)')
try: import gi.repository.GLib
except ImportError: errlist.append('gi.repository.GLib (gi submodule)')
try:import netifaces
except ImportError: errlist.append('netifaces')

host = ''
port = 9
interface = ''
init = '\xff'*6
count = 0
lastuid = -1

if len(errlist) > 0:
    sys.stderr.write('\n\033[31;1m'+'Error: '+'\033[0m'+'The following Python 2.x modules are not installed:'+'\n\n')
    for item in errlist:
        sys.stderr.write(item+'\n')
    sys.stderr.write('\n'+'Please install them and try again, see README for more information on how to do this.'+'\n\n')
    sys.exit(1)

if port < 1024 and not os.getuid() == 0:
    sys.exit('\n\033[31;1m'+'Error: '+'\033[0m'+'You are not root user. You need to run this script as root for access to priviledged ports.'+'\n')

if len(sys.argv) > 1 and sys.argv[1] == '--debug':debug = True
else: debug = False

def opensoc(h=None,p=None,b=None):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if b == 'bind': s.bind((h, p))
    return s

def getmac():
    # potential standard-lib method:
    # for default gateway read /proc/net/route
    # for MAC address read /sys/class/net/[interface]/address
    if interface == '':
        defgate = netifaces.gateways()['default']
        inter = defgate[defgate.keys()[0]][1]
    else: inter = interface
    mac = netifaces.ifaddresses(inter)[netifaces.AF_LINK][0]['addr']
    return mac

def chkmagic(data):
    if data.startswith(init):
        mac = getmac()
        magic = data
        targetmacbin = data[96:]
        targetmacint = struct.unpack('>6B',targetmacbin)
        count = 0
        for item in targetmacint:
            item = format(item,'x')
            if count == 0: targetmachex = item
            else: targetmachex = targetmachex+':'+item
            count = count + 1
        if targetmachex == mac and magic == init+(targetmacbin*16):
            return True

def getactivesysd():
    bus = dbus.SystemBus()
    sysd = bus.get_object('org.freedesktop.login1','/org/freedesktop/login1')
    seslist = sysd.ListSessions(dbus_interface='org.freedesktop.login1.Manager')

    sesobs = list()
    for session in seslist:
        sesobs.append(session[4])

    for sesob in sesobs:
        ses = bus.get_object('org.freedesktop.login1', sesob)
        props = dbus.Interface(ses, 'org.freedesktop.DBus.Properties')
    
        uid = props.Get('org.freedesktop.login1.Session','User')[0]
        if props.Get('org.freedesktop.login1.Session','Remote'): continue
        if props.Get('org.freedesktop.login1.Session','Active'): return uid

def getactiveck():
    bus = dbus.SystemBus()
    ck = bus.get_object('org.freedesktop.ConsoleKit','/org/freedesktop/ConsoleKit/Manager')
    sesobs = ck.GetSessions(dbus_interface='org.freedesktop.ConsoleKit.Manager')

    for sesob in sesobs:
        ses = bus.get_object('org.freedesktop.ConsoleKit', sesob)
        props = dbus.Interface(ses, 'org.freedesktop.DBus.Properties')
    
        uid = props.Get('org.freedesktop.ConsoleKit.Session','user')
        if not props.Get('org.freedesktop.ConsoleKit.Session','is-local'): continue
        if props.Get('org.freedesktop.ConsoleKit.Session','active'): return uid

def iskodirunning():
    rpc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try: rpc.connect(('localhost', 9090))
    except socket.error:
        return False
    else:
        rpc.sendall('{"jsonrpc":"2.0","method":"JSONRPC.Ping","id":1}')
        while True:
            data,addr = rpc.recvfrom(1024)
            if data:
                break
        rpc.close()
        thing = json.loads(data)
        if thing['result'] == 'pong':            
            return True
        else:
            return False # should report an error here, since this should not happen
    finally: rpc.close()

def signalhandler(ret):
    loop.quit()
    if debug: print 'Kodi has exited (signal received) with return code:',ret

while True:
    s = opensoc(host,port,'bind')
    found = False

    while not found:
        # UDP max packet size is 65536, magic packet size is 102 for 48-bit MAC addresses
        conn1 = s.recv(102)
        if debug: print 'Received a packet...'

        # Yatse sends some text, then magic packet. Kore just sends two identical magic packets.
        if conn1 == 'YatseStart-Xbmc' or conn1.startswith(init):
            s.settimeout(1) # possibly needs increasing
            try: conn2 = s.recv(102)
            except socket.timeout: continue
            finally: s.settimeout(None)
            if debug: print 'This one looks like a WOL packet'
        if conn1 == 'YatseStart-Xbmc': found = chkmagic(conn2)
        else:
            found1 = chkmagic(conn1)
            if found1: found = chkmagic(conn2)

    if debug: print 'Now found 2nd packet and validated packet(s)'
    if debug: print 'Checking to see if Kodi is already running'
    # Check if ANY instance of Kodi running
    running = iskodirunning()
    if running: continue

    s.close()
    
    if debug: print 'Now trying to start Kodi over D-Bus'
    if lastuid == -1: pass
    else: lastuid = uid
    try: uid = getactivesysd()
    except: uid = getactiveck()
    home = pwd.getpwuid(uid)[5]
    fname = home + '/.amwaketool/dbus_session_bus_address'
    busaddr = open(fname,'r').read()[25:]

    # We have to de-elevate privileges to connect to Session Bus
    os.setresgid(uid, uid, 0)
    os.setresuid(uid, uid, 0)

    if count < 1 or not lastuid == uid:
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True) # Applies to newly instantiated buses only
        bus = dbus.bus.BusConnection(busaddr)
        service = bus.get_object('org.amwaketool','/')        
        signal = service.connect_to_signal('endkodi',signalhandler,dbus_interface='org.amwaketool')
        count = count + 1
    else:
        service = bus.get_object('org.amwaketool','/')
    
    pid = service.startkodi()
    if debug: print 'Kodi has started with PID =',pid

    loop = gi.repository.GLib.MainLoop()
    run = loop.run()
    
    service.exit()

    # Finished with Session Bus, go back to root
    os.setresgid(0, 0, 0)
    os.setresuid(0, 0, 0)

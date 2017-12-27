#! /usr/bin/python2

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
try: import dbus
except ImportError: errlist.append('dbus')
try: import dbus.service
except ImportError: errlist.append('dbus.service (dbus submodule)')
try: import dbus.mainloop.glib
except: errlist.append('dbus.mainloop.glib (dbus submodule)')
try: import gi.repository.GLib
except: errlist.append('gi.repository.GLib (gi submodule)')
import subprocess
import sys
import signal
import os

if len(errlist) > 0:
    sys.stderr.write('\n\033[31;1m'+'Error: '+'\033[0m'+'The following Python 2.x modules are not installed:'+'\n\n')
    for item in errlist:
        sys.stderr.write(item+'\n')
    sys.stderr.write('\n'+'Please install them and try again, see README for more information on how to do this.'+'\n\n')
    sys.exit(1)

if len(sys.argv) > 1 and sys.argv[1] == '--debug':debug = True
else: debug = False

bname = 'org.amwaketool' # bus and interface name

class waketool(dbus.service.Object):

    def sighandler(self):
        if debug: print 'wait'
        ret = obj.wait()
        self.endkodi(ret)

    @dbus.service.method(bname,in_signature='',out_signature='n')
    def startkodi(self):
        global obj
        obj = subprocess.Popen('kodi')
        servicepid = os.getpid()
        os.kill(servicepid,10)
        return obj.pid

    @dbus.service.signal(bname)
    def endkodi(self,ret):
        if debug: print 'emit signal'

    @dbus.service.method(bname)
    def exit(self): loop.quit()

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True) # Applies to newly instantiated buses only

sesbus = dbus.SessionBus() # So this must be here
bn = dbus.service.BusName(bname,sesbus)
ms = waketool(sesbus,'/')
gi.repository.GLib.unix_signal_add(gi.repository.GLib.PRIORITY_HIGH, signal.SIGUSR1, ms.sighandler)
loop = gi.repository.GLib.MainLoop()
loop.run()


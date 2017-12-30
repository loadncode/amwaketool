#!/usr/bin/python3

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

from __future__ import print_function

import pwd
import re
import os
import errno
import sys

if not os.getuid() == 0: sys.exit('\n\033[31;1m'+'Error: '+'\033[0m'+'You are not root user.'+'\n')

data = open('/etc/login.defs','r').read()
minuid = re.findall('^UID_MIN\s+([0-9]+)',data,re.MULTILINE)
try: minuid = int(minuid[0])
except: minuid = 1000
maxuid = re.findall('^UID_MAX\s+([0-9]+)',data,re.MULTILINE)
try: maxuid = int(maxuid[0])
except: maxuid = 60000

homelist = list()
for user in pwd.getpwall():
    if minuid <= user[2] <= maxuid: homelist.append(user[5])

for home in homelist:
    try: os.remove(home+'/.amwaketool/dbus_session_bus_address')
    except OSError: pass
    try: os.rmdir(home+'/.amwaketool')
    except OSError as e:
        if e.errno == errno.ENOTEMPTY:
            print('\033[31;1m'+'Warning: '+'\033[0m'+'cannot remove '+'\033[3m'+home+'/.amwaketool'+'\033[0m'+', directory is not empty')

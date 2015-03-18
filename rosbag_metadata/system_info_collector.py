# The MIT License (MIT)
#
# Copyright (c) 2015 Hordur K. Heidarsson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# System data:
## git
### search through ros package path, search for git repositories, get version
## system
### uname -a
###

import os
import rospkg
from rospkg.common import PACKAGE_FILE
from rospkg.rospack import ManifestManager
import platform
import re
import subprocess
import git
import datetime
import socket
import netifaces

# http://stackoverflow.com/questions/8110310/simple-way-to-query-connected-usb-devices-info-in-python
def get_usb_devices():
    device_re = re.compile("Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<id>\w+:\w+)\s(?P<tag>.+)$", re.I)
    df = subprocess.check_output("lsusb", shell=True)
    devices = []
    for i in df.split('\n'):
        if i:
            info = device_re.match(i)
            if info:
                dinfo = info.groupdict()
                dinfo['device'] = '/dev/bus/usb/%s/%s' % (dinfo.pop('bus'), dinfo.pop('device'))
                devices.append(dinfo)
    return devices

def get_ip_info():
    res = {}
    for iface in netifaces.interfaces():
        res[iface] = netifaces.ifaddresses(iface)
    return res

class SystemInfoCollector():
    def __init__(self, system_info_all=True, system_info_usb=True, system_info_git=True, system_info_ros=True, system_info_env=True, system_info_full_env=False, system_info_ip=True, **kwargs):

        self.use_usb = system_info_usb or system_info_all
        self.use_git = system_info_git or system_info_all
        self.use_ros = system_info_ros or system_info_all
        self.use_env = system_info_env or system_info_all
        self.use_full_env = system_info_full_env or system_info_all
        self.use_ip = system_info_ip or system_info_all

        self.rospack = rospkg.RosPack()
        self.rosstack = rospkg.RosStack()
        self.mm = ManifestManager(PACKAGE_FILE)

    def get_ros_package_version(self, stack_name):
        # copied from https://github.com/ros-infrastructure/rospkg/blob/master/scripts/rosversion
        try:
            version = self.rosstack.get_stack_version(stack_name)
        except rospkg.ResourceNotFound as e:
            try:
                # hack to make it work with wet packages
                path = self.mm.get_path(stack_name)
                package_manifest = os.path.join(path, 'package.xml')
                if os.path.exists(package_manifest):
                    from xml.etree.ElementTree import ElementTree
                    try:
                        root = ElementTree(None, package_manifest)
                        version = root.findtext('version')
                        return version
                    except Exception:
                        pass
            except rospkg.ResourceNotFound as e:
                return None
        return None

    def get_git_repo_info(self, path):
        res = {}

        repo = git.Repo(path)
        g = repo.git

        res['branch'] = repo.head.ref.name
        res['rev'] = g.rev_parse('HEAD')

        log = repo.head.ref.log()
        if len(log) > 0:
            last_log = log[-1]
            res['rev_time'] = datetime.datetime.fromtimestamp(last_log.time[0]).__str__()

        res['remotes'] = {}
        for r in repo.remotes:
            res['remotes'][r.name] = {'url': r.url}

        return res

    def find_git_repos(self, paths):
        res = {}
        for p in paths:
            if not os.path.exists(p):
                continue
            g = git.Git(p)
            try:
                git_root = g.rev_parse(show_toplevel=True)
                if not res.has_key(git_root):
                    res[git_root] = self.get_git_repo_info(git_root)
            except git.GitCommandError:
                pass
        return res


    def get_ros_info(self):
        res = {}

        rospack = rospkg.RosPack()

        if 'ROS_DISTRO' in os.environ:
            res['distro_name'] = os.environ['ROS_DISTRO']

        res['package_versions'] = {}
        for p in rospack.list():
            res['package_versions'][p] = self.get_ros_package_version(p)

        if self.use_git:
            res['git'] = self.find_git_repos(os.environ['ROS_PACKAGE_PATH'].split(':'))

        # search for git repositories within ros package path

        return res

    def get_data(self):
        res = {}
        if self.use_env:
            res['env'] = self.get_env(only_ros=not self.use_full_env)

        if self.use_ros:
            res['ros'] = self.get_ros_info()

        res['system'] = self.get_system_info()
        return res

    def get_env(self, only_ros=True):
        d = os.environ.copy()
        if only_ros:
            for k in d.keys():
                if not k.startswith('ROS_'):
                    del d[k]
                if k == 'ROS_PACKAGE_PATH':
                    d[k] = d[k].split(':')
        return d

    def get_system_info(self):
        res = {}
        res['platform'] = platform.platform()
        res['hostname'] = socket.gethostname()

        if self.use_ip:
            res['ip'] = get_ip_info()

        if self.use_usb:
            res['usb'] = get_usb_devices()
        return res

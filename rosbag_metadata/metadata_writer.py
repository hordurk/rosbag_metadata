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

import rosbag
import std_msgs
import rospy

import os.path
import yaml
import re
import datetime

from .config import *
from .utils import *

class BagMetadataUtility(object):
    """docstring for BagMetadataUtility"""
    def __init__(self, target, default_topic=DEFAULT_TOPIC, metadata_filename=METADATA_FILENAME, **kwargs):
        super(BagMetadataUtility, self).__init__()
        self.target = target
        self.metadata_filename = metadata_filename
        self.default_topic = default_topic

    def is_bag_file(self, path):
        if path.endswith('.bag'): #assume it is a bagfile if it ends with .bag
            return True

        # Do some actual file inspection?
        # Open with rosbag? (does that take time if file is big?)

        return False

    def get_rosbag_info(self, path):
        res = {}
        path = os.path.normpath(os.path.join(os.getcwd(), path))
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        for f in os.listdir(path):
            if f.endswith('.bag'):
                res[f] = self.get_info(os.path.join(path,f))
        return res


    def dict_to_yaml(self, data):
        data['_metadata_info'] = {'creator': PROG, 'about': ABOUT,
         'version': VERSION, 'url': URL, 'date': '%s' % datetime.datetime.now(),
         'path': self.target}
        return yaml.dump(data)

    def write_metadata_file(self, filename, metadata_string, overwrite_existing=False):

        if os.path.exists(filename):
            if overwrite_existing == OVERWRITE_ASK: # Ask
                overwrite_existing = query_yes_no("Overwrite existing file '%s'?" % filename, 'n')
            if not overwrite_existing:
                return None
        with open(filename,'w') as f:
            f.write(metadata_string)
        return (filename, )

    def write_metadata(self, filename, metadata, overwrite_existing=False):

        if isinstance(metadata, dict): #convert dict to yaml
            metadata = self.dict_to_yaml(metadata)

        if os.path.isdir(filename):
            return self.write_metadata_file(os.path.join(filename, self.metadata_filename), metadata, overwrite_existing=overwrite_existing)
        elif not os.path.exists(filename):
            return self.write_metadata_file(filename, metadata, overwrite_existing=overwrite_existing)
        else:
            try:
                return self.inject_to_bag(filename, metadata)
            except rosbag.bag.ROSBagException, e:
                if e.value == 'This does not appear to be a bag file' or e.value == 'empty file':
                    if overwrite_existing:
                        return self.write_metadata_file(filename, metadata, overwrite_existing=overwrite_existing)
                else:
                    raise

        # Metadata not written
        return None


    def inject_to_bag(self, bagfile_name, metadata):
        with rosbag.Bag(bagfile_name, 'a') as bag:
            metadata_msg = std_msgs.msg.String(data=metadata)
            t = rospy.Time(bag.get_end_time())
            bag.write(self.default_topic, metadata_msg, t + rospy.rostime.Duration(0, 1))


    def find_split_files(self, bagfile_name):
        path = os.path.dirname(bagfile_name)
        info = get_info(bagfile_name, freq=False)

    def extract_from_bag(self, bagfile_name, use_yaml=True):
        found = False
        with rosbag.Bag(bagfile_name, 'r') as bag:
            for msg_topic, msg, t in bag.read_messages(topics=[self.default_topic,]):
                if msg_topic == self.default_topic:
                    found = True
                    break
            if found:
                if use_yaml: # Try to parse data as yaml unless told not to
                    try:
                        return (bagfile_name, yaml.load(msg.data))
                    except:
                        pass
                return (bagfile_name, msg.data)
        return None

    def extract_from_dir(self, dirname, search_bags=True, find_all=False):
        res = []
        filename = os.path.join(dirname, self.metadata_filename)
        if os.path.exists(filename):
            res.append(self.extract_from_file(filename))
            if not find_all:
                return res

        if search_bags:
            for f in os.listdir(dirname):
                if f.endswith('.bag'):
                    r = self.extract_from_bag(os.path.join(dirname,f))
                    if r is not None:
                        res.append(r)
                        if not find_all:
                            return res

        return res

    def extract_from_file(self, filename):
        # try reading the file
        with open(filename, 'r') as f:
            data = f.read()
            return (filename, yaml.load(data))
        return None

    def extract(self, filename, use_yaml=True, find_all=False):
        res = []

        if not os.path.exists(filename):
            return res

        # check if directory, then search for metadata files
        if os.path.isdir(filename):
            res = self.extract_from_dir(filename,find_all=find_all)
        else:
            try:
                res.append(self.extract_from_bag(filename, use_yaml=use_yaml))
            except rosbag.bag.ROSBagException, e:
                if e.value == 'This does not appear to be a bag file' or e.value == 'empty file':
                    res.append(self.extract_from_file(filename))
                else:
                    raise

        if res is None or len(res) == 0 or res[0] is None:
            return []

        return res

    def get_info(self, bagfile_name, freq=True):
        b = rosbag.Bag(bagfile_name, 'r',skip_index=not freq)
        return yaml.load(b._get_yaml_info())


    def get_full_info(self, bagfile_name, freq=True):
        return dict(self.get_info(bagfile_name, freq=freq).items() + self.extract(bagfile_name, use_yaml=True).items())

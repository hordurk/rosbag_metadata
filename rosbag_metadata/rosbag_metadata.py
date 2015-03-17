#!/usr/bin/env python

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

from __future__ import print_function

import os.path
import sys

import yaml

from .utils import *
from .metadata_writer import BagMetadataUtility
from .system_info_collector import SystemInfoCollector
from .config import *


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Read or write metadata to bagfiles or textfiles.')
    parser.add_argument('path', metavar='path', type=str, help='Target (bagfile, textfile or directory)')
    parser.add_argument('--read', dest='read', action='store_true', help='Only read metadata, no writing.')
    parser.add_argument('--clear', dest='clear', action='store_true', help='Do not read existing metadata, start fresh.')
    parser.add_argument('--debug', dest='debug', action='store_true', help='Output debug info')
    parser.add_argument('--write-rosbag-info', dest='rosbag_info', action='store_true', help="Runs 'rosbag info --freq' on each bag files in the directory and saves along with metadata (does not apply to bagfile targets)")
    parser.add_argument('--no-system-info', dest='system_info', action='store_false', help='Do not collect any system info as part of written metadata')
    parser.add_argument('--find-all', dest='find_all', action='store_true', help='Searches for all possible metadata for given path (only applies to directory targets)')
    args = parser.parse_args()

    bmu = BagMetadataUtility()

    found_data = bmu.extract(args.path, find_all=args.find_all)
    if len(found_data) == 0 or args.clear:
        existing_data = {}
    else:
        for d in found_data:
            pass # pick newest
        existing_data = found_data[0][1]

    if args.read:
        for d in found_data:
            print('Found the following data in %s:' % d[0])
            print(yaml.dump(d[1]))
        exit(0)

    data = {}

    print('Use Ctrl+D to skip field instead of using default value.')

    try:
        for k in DEFAULT_FIELDS:
            try:
                data[k] = query(k,existing_data.get(k))
            except EOFError:
                print('')
                pass

        for k in existing_data.keys():
            if k in DEFAULT_FIELDS or k in SYSTEM_FIELDS:
                continue
            try:
                data[k] = query(k, existing_data.get(k))
            except EOFError:
                print('')
                pass

        print('\n===Extra Fields===')

        while True:
            field = query('Field name')
            if field is not None and len(field) > 0:
                field_data = query(field)
                if field_data is not None and len(field_data) > 0:
                    data[field] = field_data
                else:
                    break
            else:
                break
    except (KeyboardInterrupt, EOFError):
        print('')
        pass
    except:
        raise

    if args.system_info:
        print('Collecting system/environment metadata')
        data[SYSTEM_INFO_FIELD] = SystemInfoCollector().get_data()

    if args.rosbag_info and not bmu.is_bag_file(args.path):
        data[BAGS_INFO_FIELD] = bmu.get_rosbag_info(args.path)

    # Prune data for empty keys
    for k in data.keys():
        if data[k] is None or data[k] == '':
            del data[k]

    if args.debug:
        print('===============')
        print('About to write:')
        print(bmu.dict_to_yaml(data))
        print('===============')

    bmu.write_metadata(args.path, data, overwrite_existing=OVERWRITE_ASK)

if __name__ == '__main__':
    main()

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
import ast

import yaml

from .utils import *
from .metadata_writer import BagMetadataUtility
from .system_info_collector import SystemInfoCollector
from .config import *

import ConfigParser



def print_once(s):
    if not hasattr(print_once, 'd'):
        print_once.d = set()
    if not s in print_once.d:
        print(s)
        print_once.d.add(s)


def main():

    import argparse
    conf_parser = argparse.ArgumentParser(add_help=False)
    conf_parser.add_argument('-c', '--config', dest='config', type=str, help='Config file', default='~/.ros/rosbag_metadata.conf')
    args, remaining_argv = conf_parser.parse_known_args()

    bool_config_options = ('clean', 'write_rosbag_info', 'system_info', 'system_info_all', 'system_info_usb',
        'system_info_git', 'system_info_ros', 'system_info_env', 'system_info_full_env', 'system_info_ip', 'find_all',
        'debug', 'ask_template_defaults', 'extra_fields')
    allowed_config_options = bool_config_options + ('template',)

    config = {}
    default_fields = DEFAULT_FIELDS


    if args.config and os.path.exists(os.path.expanduser(args.config)):
        config_parser = ConfigParser.SafeConfigParser(allow_no_value=True)
        config_parser.read([os.path.expanduser(args.config)])
        config = dict(config_parser.items("config"))


        for k in config.keys():

            # Only allow certain options to be read from config
            if not k in allowed_config_options:
                del config[k]
                continue
            if k in bool_config_options:
                config[k] = config_parser.getboolean('config',k)

        if config_parser.has_section('default_fields'):
            default_fields = dict(config_parser.items("default_fields"))

            # Remove fields that conflict with system reserved fields
            for k in default_fields.keys():
                if k in SYSTEM_FIELDS:
                    del default_fields[k]

        # read config file

    parser = argparse.ArgumentParser(parents=[conf_parser,], description='Read or write metadata to bagfiles or textfiles.', formatter_class=argparse.RawDescriptionHelpFormatter,)

    parser.add_argument('path', metavar='path', type=str, help='Target (bagfile, yamlfile or directory)')

    mutexgroup = parser.add_mutually_exclusive_group()
    mutexgroup.add_argument('-r', '--read', dest='not_used', action='store_true', help='Only read metadata (default).')
    mutexgroup.add_argument('-w', '--write', dest='read', action='store_false', help='Write metadata.')

    # Write options
    writegroup = parser.add_argument_group('Write options')
    writegroup.add_argument('-t', '--template', dest='template', type=str, help='')
    writegroup.add_argument('--clean', dest='clean', action='store_true', help='Do not read existing metadata, start fresh.')
    writegroup.add_argument('--write-rosbag-info', dest='write_rosbag_info', action='store_true', help="Runs 'rosbag info --freq' on each bag files in the directory and saves along with metadata (does not apply to bagfile targets)")
    writegroup.add_argument('--ask-template-defaults', dest='ask_template_defaults', action='store_true', help='Ask for values of fields defined in template even if they have a default value.')
    writegroup.add_argument('--no-extra-fields', dest='extra_fields', action='store_false', help='Do not prompt for extra fields.')
    writegroup.add_argument('-y', '--yes', dest='no_prompt', action='store_true', help='Do not prompt for overwriting files.')

    systemgroup = parser.add_argument_group('System metadata options')
    systemgroup.add_argument('--no-system-info', dest='system_info', action='store_false', help='Do not collect any system info as part of written metadata')
    systemgroup.add_argument('--all-system-info', dest='system_info_all', action='store_true', help='Collect all system info for metadata (overrides specific options)')
    systemgroup.add_argument('--no-usb', dest='system_info_usb', action='store_false', help='Do not collect usb device info as part of system metadata')
    systemgroup.add_argument('--no-git', dest='system_info_git', action='store_false', help='Do not collect git repository info as part of written metadata')
    systemgroup.add_argument('--no-ros', dest='system_info_ros', action='store_false', help='Do not collect ros info as part of written metadata')
    systemgroup.add_argument('--no-env', dest='system_info_env', action='store_false', help='Do not collect environment variables as part of written metadata')
    systemgroup.add_argument('--no-full-env', dest='system_info_full_env', action='store_false', help='Only collect ROS environment variables as written metadata')
    systemgroup.add_argument('--no-ip', dest='system_info_ip', action='store_false', help='Do not collect IP information as part of written metadata')

    # Both options
    parser.add_argument('-a', '--find-all', dest='find_all', action='store_true', help='Searches for all possible metadata for given path (only applies to directory targets)')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', help='Output debug info')
    parser.add_argument('-v', '--version', action='version', version='rosbag_metadata %s' % VERSION)


    # Use data from config to set defaults
    parser.set_defaults(**config)

    args = parser.parse_args(remaining_argv)


    # bmu only uses non command-line options from the config, so we pass config directly (instead of vars(args))
    bmu = BagMetadataUtility(**config)

    found_data = bmu.extract(args.path, find_all=args.find_all)
    if len(found_data) == 0 or args.clean:
        existing_data = {}
    else:
        for d in found_data:
            pass # pick newest
        existing_data = found_data[0][1]

    skip_template_defaults = []

    if args.template:
        template = {}
        try:
            template = yaml.load(file(args.template, 'r'))
            for k in template.keys():
                if template[k] is not None:
                    skip_template_defaults.append(k)
            existing_data.update(template)
        except:
            print("Error loading template '%s'. Exiting." % args.template)
            raise
            exit(1)


    if args.read:
        for d in found_data:
            print('Found the following data in %s:' % d[0])
            print(yaml.dump(d[1]))
        exit(0)

    data = {}

    for k in existing_data.keys():
        if k in SYSTEM_FIELDS:
            del existing_data[k]
        if not args.ask_template_defaults and k in skip_template_defaults:
            if type(existing_data[k]) is dict and 'ask' in existing_data[k].keys() and existing_data[k]['ask']:
                existing_data[k] = existing_data[k]['value']
                continue
            print_once('\nUsing defaults from template:')
            print('%s=%s' % (k,existing_data[k]))
            data[k] = existing_data[k]
            del existing_data[k]

    try:
        if not type(default_fields) is dict:
            d = {}
            for k in default_fields:
                d[k] = None
            default_fields = d

        for k in set(tuple(default_fields.keys()) + tuple(existing_data.keys())):
            try:
                if not args.ask_template_defaults and k in skip_template_defaults:
                    continue

                print_once('\nUse Ctrl+D to leave field empty instead of using default value.')
                print_once("\nPlease fill out the following:")
                data[k] = query(k,default_fields.get(k) or existing_data.get(k))
            except EOFError:
                print('')
                pass

        if args.extra_fields:
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
        print('\nCollecting system/environment metadata')
        data[SYSTEM_INFO_FIELD] = SystemInfoCollector(**vars(args)).get_data()

    if args.write_rosbag_info and not bmu.is_bag_file(args.path):
        data[BAGS_INFO_FIELD] = bmu.get_rosbag_info(args.path)

    # Prune data of empty keys
    for k in data.keys():
        if data[k] is None or data[k] == '':
            del data[k]

    if args.debug:
        print('===============')
        print('About to write:')
        print(bmu.dict_to_yaml(data))
        print('===============')

    if args.no_prompt:
        overwrite_existing = True
    else:
        overwrite_existing = OVERWRITE_ASK
    bmu.write_metadata(args.path, data, overwrite_existing=overwrite_existing)

if __name__ == '__main__':
    main()

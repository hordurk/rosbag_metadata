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

ABOUT = 'bag_metadata'
URL = 'https://github.com/hordurk/rosbag_metadata'
VERSION = '0.1.4'
OVERWRITE_ASK = -1

METADATA_INFO_FIELD = '_metadata_info'
SYSTEM_INFO_FIELD = '_system_info'
BAGS_INFO_FIELD = '_bags'

SYSTEM_FIELDS = (METADATA_INFO_FIELD, SYSTEM_INFO_FIELD, BAGS_INFO_FIELD)

DEFAULT_FIELDS = ('description',)

METADATA_FILENAME = 'metadata.yaml'
DEFAULT_TOPIC = '/metadata'

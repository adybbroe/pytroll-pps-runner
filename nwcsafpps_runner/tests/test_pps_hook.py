#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2020 Pytroll developers

# Author(s):

#   Adam.Dybbroe <adam.dybbroe@smhi.se>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Testing the pps-hook code for the creation of a posttroll message.

The message is created from metadata partly read from a yaml config file.
"""

import os
from datetime import datetime, timedelta
import pytest
import unittest
from unittest.mock import patch, Mock, MagicMock
import yaml
import nwcsafpps_runner
from nwcsafpps_runner.pps_posttroll_hook import MANDATORY_FIELDS_FROM_YAML


START_TIME1 = datetime(2020, 10, 28, 12, 0, 0)
END_TIME1 = datetime(2020, 10, 28, 12, 0, 0) + timedelta(seconds=86)

# Test yaml content:
TEST_YAML_CONTENT_OK = """
pps_hook:
    post_hook: !!python/object:nwcsafpps_runner.pps_posttroll_hook.PPSMessage
      description: "This is a pps post hook for PostTroll messaging"
      metadata:
        posttroll_topic: "PPSv2018"
        station: "norrkoping"
        output_format: "CF"
        level: "2"
        variant: DR
"""
TEST_YAML_CONTENT_INSUFFICIENT = """
pps_hook:
    post_hook: !!python/object:nwcsafpps_runner.pps_posttroll_hook.PPSMessage
      description: "This is a pps post hook for PostTroll messaging"
      metadata:
        posttroll_topic: "PPSv2018"
        station: "norrkoping"
        variant: DR
"""


def create_instance_from_yaml(yaml_content_str):
    """Create a PPSMessage instance from a yaml file."""
    from nwcsafpps_runner.pps_posttroll_hook import PPSMessage
    return yaml.load(yaml_content_str, Loader=yaml.UnsafeLoader)


class TestPPSMessage(unittest.TestCase):
    """Test the functionality of the PPSMessage object."""

    def setUp(self):
        self.pps_message_instance_from_yaml_config = create_instance_from_yaml(TEST_YAML_CONTENT_OK)

    def test_class_instance_can_be_called(self):
        """Test that the PPSMessage can be instantiated and called."""
        mymock = MagicMock()
        mymock.send = Mock(return_value=None)

        test_mda = {'filename': 'xxx', 'start_time': None, 'end_time': None, 'sensor': 'viirs'}
        with patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage', return_value=mymock) as mypatch:
            value = self.pps_message_instance_from_yaml_config['pps_hook']['post_hook'](0, test_mda)

        mypatch.assert_called_once()


class TestPostTrollMessage(unittest.TestCase):
    """Test the functionality of the PostTrollMessage object."""

    def setUp(self):
        self.pps_message_instance_from_yaml_config_ok = create_instance_from_yaml(TEST_YAML_CONTENT_OK)
        self.pps_message_instance_from_yaml_config_fail = create_instance_from_yaml(TEST_YAML_CONTENT_INSUFFICIENT)

        self.metadata = {'posttroll_topic': 'PPSv2018', 'station': 'norrkoping',
                         'output_format': 'CF',
                         'level': '2', 'variant': 'DR'}
        self.metadata_with_filename = {'posttroll_topic': 'PPSv2018', 'station': 'norrkoping',
                                       'output_format': 'CF',
                                       'level': '2', 'variant': 'DR', 'filename': '/tmp/xxx'}
        self.metadata_with_start_and_end_times = {'posttroll_topic': 'PPSv2018',
                                                  'station': 'norrkoping', 'output_format': 'CF',
                                                  'level': '2', 'variant': 'DR',
                                                  'start_time': None, 'end_time': None}
        self.metadata_with_platform_name = {'posttroll_topic': 'PPSv2018',
                                            'station': 'norrkoping', 'output_format': 'CF',
                                            'level': '2', 'variant': 'DR',
                                            'platform_name': 'npp'}

        self.mandatory_fields = MANDATORY_FIELDS_FROM_YAML

    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_filename')
    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_mandatory_parameters')
    def test_send_method(self, mandatory_param, filename):
        """Test that the message contains the mandatory fields."""
        from nwcsafpps_runner.pps_posttroll_hook import PostTrollMessage

        mandatory_param.return_value = True
        filename.return_value = True

        with patch.object(PostTrollMessage, 'publish_message', return_value=None) as mock_method_publish:
            with patch.object(PostTrollMessage, 'create_message', return_value=None) as mock_method_create:
                posttroll_message = PostTrollMessage(0, self.metadata)
                posttroll_message.send()
                self.assertEqual(mock_method_publish.call_count, 1)
                self.assertEqual(mock_method_create.call_count, 1)

        with patch.object(PostTrollMessage, 'publish_message', return_value=None) as mock_method_publish:
            with patch.object(PostTrollMessage, 'create_message', return_value=None) as mock_method_create:
                posttroll_message = PostTrollMessage(1, self.metadata)
                posttroll_message.send()
                self.assertEqual(mock_method_publish.call_count, 0)
                self.assertEqual(mock_method_create.call_count, 0)

    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_mandatory_parameters')
    def test_check_metadata_contains_filename(self, mandatory_param):
        """Test that the filename has to be included in the metadata."""
        from nwcsafpps_runner.pps_posttroll_hook import PostTrollMessage

        mandatory_param.return_value = True

        with pytest.raises(KeyError) as exec_info:
            posttroll_message = PostTrollMessage(0, self.metadata)

        exception_raised = exec_info.value
        self.assertEqual(str(exception_raised), "'filename'")

        posttroll_message = PostTrollMessage(0, self.metadata_with_filename)

    @patch('socket.gethostname')
    def test_create_message(self, socket_gethostname):
        """Test creating a message with header/topic, type and content."""
        from nwcsafpps_runner.pps_posttroll_hook import PostTrollMessage

        socket_gethostname.return_value = 'TEST_SERVERNAME'

        metadata = {'posttroll_topic': 'PPSv2018',
                    'station': 'norrkoping',
                    'output_format': 'CF',
                    'level': '2',
                    'variant': 'DR',
                    'start_time': START_TIME1, 'end_time': END_TIME1,
                    'sensor': 'viirs',
                    'filename': '/tmp/xxx',
                    'platform_name': 'npp'}

        posttroll_message = PostTrollMessage(0, metadata)
        uid = os.path.basename(metadata.get('filename'))

        with patch.object(nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage, 'is_segment', return_value=True) as mock_method:
            result_message = posttroll_message.create_message('OK')

        mock_method.assert_called_once()
        message_header = "/segment/CF/2/UNKNOWN/norrkoping/offline/polar/direct_readout/"
        message_content = {'posttroll_topic': 'PPSv2018',
                           'station': 'norrkoping',
                           'variant': 'DR',
                           'start_time': START_TIME1,
                           'end_time': END_TIME1,
                           'sensor': 'viirs',
                           'uri': 'ssh://TEST_SERVERNAME' + metadata['filename'],
                           'uid': uid,
                           'data_processing_level': '2',
                           'format': 'CF',
                           'status': 'OK',
                           'platform_name': 'Suomi-NPP'}
        message_type = 'file'
        expected_message = {'header': message_header, 'type': message_type, 'content': message_content}

        self.assertDictEqual(expected_message, result_message)

        with patch.object(PostTrollMessage, 'is_segment', return_value=False) as mock_method:
            result_message = posttroll_message.create_message('OK')

        message_header = "/CF/2/UNKNOWN/norrkoping/offline/polar/direct_readout/"
        mymessage = {'header': message_header, 'type': message_type, 'content': message_content}

        self.assertDictEqual(mymessage, result_message)

    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_filename')
    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_mandatory_parameters')
    def test_start_and_end_times_cannot_be_none(self, mandatory_param, filename):
        """Test that the message contains start_time and end_time which cannot be None."""
        from nwcsafpps_runner.pps_posttroll_hook import PostTrollMessage

        mandatory_param.return_value = True
        filename.return_value = True

        posttroll_message = PostTrollMessage(0, self.metadata_with_start_and_end_times)
        with pytest.raises(Exception) as exec_info:
            posttroll_message.get_granule_duration()

        self.assertTrue(exec_info.type is TypeError)
        exception_raised = exec_info.value
        self.assertEqual(str(exception_raised), "unsupported operand type(s) for -: 'NoneType' and 'NoneType'")

    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_filename')
    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_mandatory_parameters')
    def test_get_granule_duration(self, mandatory_param, filename):
        """Test that the message contains start_time and end_time which cannot be None."""
        from nwcsafpps_runner.pps_posttroll_hook import PostTrollMessage

        mandatory_param.return_value = True
        filename.return_value = True

        metadata = self.metadata_with_start_and_end_times
        metadata['start_time'] = START_TIME1
        metadata['end_time'] = END_TIME1

        posttroll_message = PostTrollMessage(0, metadata)
        delta_t = posttroll_message.get_granule_duration()
        self.assertIsInstance(delta_t, timedelta)

        self.assertAlmostEqual(delta_t.total_seconds(), 86.0, places=5)

    def test_metadata_contains_mandatory_fields(self):
        """Test that the metadata contains the mandatory fields read from yaml configuration file."""
        # level, output_format and station are all required fields
        mda = self.pps_message_instance_from_yaml_config_ok['pps_hook']['post_hook'].metadata
        for attr in MANDATORY_FIELDS_FROM_YAML:
            self.assertIn(attr, mda)

    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_filename')
    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_mandatory_parameters')
    def test_raise_exc_if_metadata_is_missing_mandatory_fields(self, mandatory_param, filename):
        """Test that an exception is raised if the message contains the mandatory fields."""
        from nwcsafpps_runner.pps_posttroll_hook import PostTrollMessage

        mandatory_param.return_value = True
        filename.return_value = True
        # level, output_format and station are all required fields
        metadata = self.pps_message_instance_from_yaml_config_fail['pps_hook']['post_hook'].metadata
        posttroll_message = PostTrollMessage(0, metadata)

        with pytest.raises(AttributeError) as exec_info:
            posttroll_message.check_mandatory_fields()

        exception_raised = exec_info.value
        expected_exception_raised = "pps_hook must contain metadata attribute level"
        self.assertEqual(str(exception_raised), expected_exception_raised)

    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_filename')
    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_mandatory_parameters')
    @patch('socket.gethostname')
    def test_get_message_with_uri_and_uid(self, socket_gethostname, mandatory_param, filename):
        """Test that the filename has to be included in the metadata."""
        from nwcsafpps_runner.pps_posttroll_hook import PostTrollMessage

        socket_gethostname.return_value = 'TEST_SERVERNAME'
        mandatory_param.return_value = True
        filename.return_value = True

        metadata = self.metadata_with_start_and_end_times
        metadata['start_time'] = START_TIME1
        metadata['end_time'] = END_TIME1

        posttroll_message = PostTrollMessage(0, metadata)
        mymessage = posttroll_message.get_message_with_uri_and_uid()

        self.assertFalse(mymessage)

        metadata.update({'filename': '/tmp/xxx'})
        result_message = {'uri': 'ssh://TEST_SERVERNAME/tmp/xxx', 'uid': 'xxx'}

        posttroll_message = PostTrollMessage(0, metadata)
        mymessage = posttroll_message.get_message_with_uri_and_uid()

        self.assertDictEqual(mymessage, result_message)

    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_filename')
    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_mandatory_parameters')
    def test_sensor_is_viirs(self, mandatory_param, filename):
        """Test the check for sensor equals 'viirs'."""
        from nwcsafpps_runner.pps_posttroll_hook import PostTrollMessage

        mandatory_param.return_value = True
        filename.return_value = True

        metadata = self.metadata_with_start_and_end_times

        posttroll_message = PostTrollMessage(0, metadata)
        is_viirs = posttroll_message.sensor_is_viirs()
        self.assertFalse(is_viirs)

        metadata['sensor'] = 'modis'
        posttroll_message = PostTrollMessage(0, metadata)
        is_viirs = posttroll_message.sensor_is_viirs()
        self.assertFalse(is_viirs)

        metadata['sensor'] = 'viirs'
        posttroll_message = PostTrollMessage(0, metadata)
        is_viirs = posttroll_message.sensor_is_viirs()
        self.assertTrue(is_viirs)

    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_filename')
    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_mandatory_parameters')
    def test_create_message_content_from_metadata(self, mandatory_param, filename):
        """Test the creation of the message content from the inout metadata."""
        from nwcsafpps_runner.pps_posttroll_hook import PostTrollMessage

        mandatory_param.return_value = True
        filename.return_value = True

        metadata = self.metadata_with_platform_name
        posttroll_message = PostTrollMessage(0, metadata)
        msg_content = posttroll_message.create_message_content_from_metadata()
        self.assertIn('platform_name', msg_content)
        self.assertEqual(msg_content['platform_name'], 'Suomi-NPP')

        metadata.update({'platform_name': 'noaa20'})
        posttroll_message = PostTrollMessage(0, metadata)
        msg_content = posttroll_message.create_message_content_from_metadata()
        self.assertEqual(msg_content['platform_name'], 'NOAA-20')

        metadata.update({'platform_name': 'NOAA-20'})
        posttroll_message = PostTrollMessage(0, metadata)
        msg_content = posttroll_message.create_message_content_from_metadata()
        self.assertEqual(msg_content['platform_name'], 'NOAA-20')

    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_filename')
    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_mandatory_parameters')
    def test_fix_mandatory_fields_in_message(self, mandatory_param, filename):
        """Test the fix of the right output message keyword names from the mandatory fields from the yaml file."""
        from nwcsafpps_runner.pps_posttroll_hook import PostTrollMessage

        mandatory_param.return_value = True
        filename.return_value = True

        metadata = self.metadata_with_platform_name
        posttroll_message = PostTrollMessage(0, metadata)

        posttroll_message._to_send = {}
        posttroll_message.fix_mandatory_fields_in_message()

        expected = {'data_processing_level': '2', 'format': 'CF', 'station': 'norrkoping'}
        self.assertDictEqual(posttroll_message._to_send, expected)

        posttroll_message._to_send = {'level': '2',
                                      'output_format': 'CF',
                                      'station': 'norrkoping'}
        posttroll_message.fix_mandatory_fields_in_message()

        expected = {'data_processing_level': '2',
                    'level': '2',
                    'output_format': 'CF',
                    'format': 'CF',
                    'station': 'norrkoping'}
        self.assertDictEqual(posttroll_message._to_send, expected)

    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_filename')
    @patch('nwcsafpps_runner.pps_posttroll_hook.PostTrollMessage.check_metadata_contains_mandatory_parameters')
    def test_clean_unused_keys_in_message(self, mandatory_param, filename):
        """Test cleaning up the unused key/value pairs in the message."""
        from nwcsafpps_runner.pps_posttroll_hook import PostTrollMessage

        mandatory_param.return_value = True
        filename.return_value = True

        metadata = self.metadata_with_platform_name
        posttroll_message = PostTrollMessage(0, metadata)

        posttroll_message._to_send = {'data_processing_level': '2',
                                      'level': '2',
                                      'output_format': 'CF',
                                      'format': 'CF',
                                      'station': 'norrkoping'}
        posttroll_message.clean_unused_keys_in_message()
        expected = {'data_processing_level': '2',
                    'format': 'CF',
                    'station': 'norrkoping'}
        self.assertDictEqual(posttroll_message._to_send, expected)
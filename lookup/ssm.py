# (c) 2016, Bill Wang <ozbillwang(at)gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import traceback
from ansible.module_utils.ec2 import HAS_BOTO3, camel_dict_to_snake_dict
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

try:
    from botocore.exceptions import ClientError
    import boto3
except ImportError:
    pass  # will be captured by imported HAS_BOTO3


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):

        ret = {}
        response = {}

        ssm_args = terms[0].split()
        ssm_dict = {}

        if not HAS_BOTO3:
            raise AnsibleError('botocore and boto3 are required.')

        client = boto3.client('ssm')

        # lookup sample: - debug: msg="{{ lookup('ssm', 'Hello') }}"
        if len(ssm_args) == 1 and "=" not in ssm_args[0]:
            try:
                response = client.get_parameters(
                    Names=ssm_args,
                    WithDecryption=True
                )
            except ClientError as e:
                module.fail_json(msg=e.message, exception=traceback.format_exc(),
                                 **camel_dict_to_snake_dict(e.response))
        # lookup sample: - debug: msg="{{ lookup('ssm', 'Names=Hello region=us-east-1') }}"
        else:
            for param in ssm_args:
                try:
                    key, value = param.split('=')
                except ClientError as e:
                    raise AnsibleError("ssm paramter store plugin needs key=value pairs, but received %s" % terms)

                if key == "Names":
                    ssm_dict[key] = [value]
                else:
                    ssm_dict[key] = value

                ssm_dict["WithDecryption"]=True

                try:
                    response = client.get_parameters(**ssm_dict)
                except ClientError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc(),
                                    **camel_dict_to_snake_dict(e.response))

        ret.update(response)

        if ret['Parameters']:
            return [ret['Parameters'][0]['Value']]
        else:
            return None

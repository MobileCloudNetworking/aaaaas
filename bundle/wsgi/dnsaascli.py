# Copyright 2014 Copyright (c) 2013-2015, OneSource, Portugal.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

__author__ = 'Claudio Marques / Bruno Sousa - OneSource'
__copyright__ = "Copyright (c) 2013-2015, Mobile Cloud Networking (MCN) project"
__credits__ = ["Claudio Marques - Bruno Sousa"]
__license__ = "Apache"
__version__ = "1.0"
__maintainer__ = "Claudio Marques - Bruno Sousa"
__email__ = "claudio@onesource.pt, bmsousa@onesource.pt"
__status__ = "Production"

import traceback
import requests
import json


class DnsaasClientCore:
    """
    Works as a client to the API DNSaaS. This class can be employed by other MCN services, or applications that require
    services from DNSaaS.
    """
    idDomain = None
    idRecord = None

    def __init__(self, ip_api, token):
        self.version = 1
        self.token = token
        self.apiurl_dnsaas = "http://" + ip_api + ":8080"

    def do_request(self, method, path, body, token):
        """
        Method to perform requests to the DNSaaS API. Requests can include creation, delete and other operations.
        This method needs to handle requests through a REST API.
        """
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=UTF-8',
            'X-auth-token': token
        }

        try:
            """
            TODO: check error output on delete operations.
            """
            r = requests.request(method, self.apiurl_dnsaas + path, data=body, headers=headers)
        except:
            traceback.print_exc()
            return -1, "Problem with the request. Error:"

        return r.status_code, json.loads(r.text)


class DnsaasClientAction:
    """
    Class representing the object to interact with DNSaaS
    """
    __dnsaasclient = None

    def __init__(self, ip_api, token):
        self.__dnsaasclient = DnsaasClientCore(ip_api, token)

        self.__token = token

    """
    Domain Methods
    """

    def create_domain(self, domain_name, email, ttl, token):
        """
        Method used to create a domain

        :param domain_name:Domain name
        :param email: Domain administrator e-mail address
        :param ttl: Time to live
        :param token: Token
        :return: Status 1 for success, or a description of error
        """
        msg_json = {'name': domain_name, 'ttl': ttl, 'email': email}
        status, content = self.__dnsaasclient.do_request('POST', '/domains', json.dumps(msg_json), token)
        return content

    def get_domain(self, domain_name, token):
        """
        Method used to get the information regarding a domain

        :param domain_name: Domain
        :param token: token
        :return: The information of the domain
        """
        msg_json = {'domain_name': domain_name}
        status, content = self.__dnsaasclient.do_request('GET', '/domains', json.dumps(msg_json), token)
        return content

    def update_domain(self, domain_name, parameter_to_update, data, token):
        """
        Method used to update a domain information

        :param domain_name: Domain name
        :param parameter_to_update: Parameter to update, ttl, email, description
        :param data: The actual information to update
        :param token: Token
        :return: Status 1 for success, or a description of error
        """
        msg_json = {'domain_name': domain_name, 'parameter_to_update': parameter_to_update, 'data': data}
        status, content = self.__dnsaasclient.do_request('PUT', '/domains', json.dumps(msg_json), token)
        return content

    def delete_domain(self, domain_name, token):
        """
        Method used to delete a Domain

        :param domain_name: Domain name
        :param token: Token
        :return: Status 1 for success, or a description of error
        """
        msg_json = {'domain_name': domain_name}
        status, content = self.__dnsaasclient.do_request('DELETE', '/domains', json.dumps(msg_json), token)
        return content

    """
    Record Methods
    """

    def create_record(self, domain_name, record_name, record_type, record_data, token, **kwargs):
        """
        Method used to create a record

        :param domain_name: Domain name
        :param record_name: Record name
        :param record_type: Record type
        :param record_data: record data
        :param token: Token
        :param kwargs: Priority for the record
        :return: Status 1 for success, or a description of error
        """
        if record_type in ['A', 'AAAA', 'TXT', 'MX', 'PTR', 'SRV', 'NS', 'CNAME', 'SPF', 'SSHFP', 'NAPTR']:
            json_record = ''
            if record_type == 'MX':

                if 'priority' in kwargs:
                    priority = kwargs['priority']
                else:
                    priority = 10

                record_name = ''
                json_record = {'domain_name': domain_name, 'record_name': record_name, 'record_type': record_type,
                               'data': record_data, 'priority': int(priority)}

            elif record_type in ['SRV', 'NAPTR']:

                if 'priority' in kwargs:
                    priority = kwargs['priority']
                else:
                    priority = 10

                json_record = {'domain_name': domain_name, 'record_name': record_name, 'record_type': record_type,
                               'data': record_data, 'priority': int(priority)}

            elif record_type == 'NS':

                json_record = {'domain_name': domain_name, 'name': record_name, 'record_type': record_type,
                               'data': record_data}

            elif record_type in ['A', 'TXT', 'SPF', 'SSHFP', 'PTR', 'AAAA', 'CNAME']:

                json_record = {'domain_name': domain_name, 'record_name': record_name, 'record_type': record_type,
                               'data': record_data}

            status, content = self.__dnsaasclient.do_request('POST', '/records',
                                                             json.dumps(json_record, sort_keys=False), token)
            return content
        else:
            return "Unrecognized record type."

    def get_record(self, domain_name, record_name, record_type, token):
        """
        Method used to get the information regarding a domain
        Can also be used to get all records information from a domain, if record_type content is null

        :param domain_name: Domain name
        :param record_name: Record name
        :param record_type: Record type, or null
        :param token: Token
        :return: The information of the record
        """
        json_record = {'domain_name': domain_name, 'record_name': record_name, 'record_type': record_type}
        status, content = self.__dnsaasclient.do_request('GET', '/records', json.dumps(json_record, sort_keys=False),
                                                         token)

        return content

    def update_record(self, domain_name, record_name, record_type, parameter_to_update, record_data, token):
        """
        Method used to update a record information

        :param domain_name: Domain name
        :param record_name: Record Name
        :param record_type: Record type
        :param parameter_to_update: Parameter to update, 'ttl', 'description' or 'data'
        :param record_data: The actual information to update
        :param token: Token
        :return: Status 1 for success, or a description of error
        """
        msg_json = {'domain_name': domain_name, 'record_name': record_name, 'record_type': record_type,
                    'parameter_to_update': parameter_to_update, 'data': record_data}
        status, content = self.__dnsaasclient.do_request('PUT', '/records', json.dumps(msg_json, sort_keys=False),
                                                         token)
        return content

    def delete_record(self, domain_name, record_name, record_type, token):
        """
        Method used to delete a record

        :param domain_name: Domain name
        :param record_name: Record name
        :param record_type: Record type
        :param token: Token
        :return: Status 1 for success, or a description of error
        """
        json_record = {'domain_name': domain_name, 'record_type': record_type, 'record_name': record_name}

        status, content = self.__dnsaasclient.do_request('DELETE', '/records', json.dumps(json_record, sort_keys=False),
                                                         token)

        return content

    """
    Geo Map Methods
    """

    def create_geo_map(self, record_name, domain_name, geo_info, token):
        """
        Method used to create a GeoDns information file

        :param record_name: Record Name
        :param domain_name: Domain Name
        :param geo_info: A array of codes and records to redirect the request
        :param token: Token
        :return: Status 1 for success, or a description of error
        """
        json_data = {'record_name': record_name, 'domain_name': domain_name, 'geoInfo': geo_info}
        status, response = self.__dnsaasclient.do_request('POST', '/geodns', json.dumps(json_data), token)

        return response

    def append_geo_map(self, record_name, domain_name, iso_codes, token):
        """
        Method used to append a geo information to an existing file

        :param record_name: Record name
        :param domain_name: Domain name
        :param iso_codes: A array of codes and records to redirect the request
        :param token: Token
        :return: Status 1 for success, or a description of error
        """
        json_data = {'record_name': record_name, 'domain_name': domain_name, 'geoInfo': iso_codes}
        status, response = self.__dnsaasclient.do_request('PUT', '/geodns', json.dumps(json_data), token)

        return response

    def get_geo_map(self, record_name, domain_name, token):
        """
        Method used to get all information regarding a geo Map for a record

        :param record_name: Record name
        :param domain_name: Domain name
        :param token: Token
        :return: An array containing the information of the geo Map
        """
        json_data = {'record_name': record_name, 'domain_name': domain_name}
        status, response = self.__dnsaasclient.do_request('GET', '/geodns', json.dumps(json_data), token)

        return response

    def delete_geo_map(self, record_name, domain_name, token, **kwargs):
        """
        Method used to delete a geoFile

        :param record_name: Record Name
        :param domain_name:Domain Name
        :param token: Token
        :param kwargs: Array of isoCodes to delete. Defaults to False
        :return: Status 1 for success, or a description of error
        """
        if 'infoToRemove' in kwargs:
            data = kwargs['infoToRemove']
        else:
            data = False

        json_data = {'record_name': record_name, 'domain_name': domain_name, 'infoToRemove': data}
        status, response = self.__dnsaasclient.do_request('DELETE', '/geodns', json.dumps(json_data), token)

        return response
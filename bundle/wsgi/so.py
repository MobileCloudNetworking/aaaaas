#   Copyright (c) 2013-2015, Intel Performance Learning Solutions Ltd, Intel Corporation.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Sample SO.
"""

import os

from sdk.mcn import util
from sm.so import service_orchestrator
from sm.so.service_orchestrator import LOG
from sm.so.service_orchestrator import BUNDLE_DIR
import random
import threading
import time

from dnsaascli import *

#HERE = os.environ['BUNDLE_DIR']

class SOE(service_orchestrator.Execution):
    """
    Sample SO execution part.
    """

    def __init__(self, token, tenant, ready_event, stop_event):
        super(SOE, self).__init__(token, tenant)
        self.stack_id = None
        self.dss_endpoint = None
        region_name = 'UBern'

        #start DNSaaS support
        self.ready_event = ready_event
        self.stop_event = stop_event
        self.aaaDomainName = 'mcn.com'
        self.recOpenam = 'aaa-openam-instance'
        self.recInfoOpenam = None
        self.recProfile = 'aaa-profile-instance'
        self.recInfoProfile = None
        self.dns_api = None
        self.dns_forwarder = None
        self.dns_info_configured = False
        self.dnsaas = None
        self.time_wait=20
        self.time_wait_after_dns=60
        #end DNSaaS support

        self.deployer = util.get_deployer(token,
                                          url_type='public',
                                          tenant_name=tenant,
                                          region=region_name)

    def design(self):
        """
        Do initial design steps here.
        """
        LOG.info('Executing design - nothing to do here')

    def deploy(self, attributes=None):
        """
        deploy SICs.
        """
        LOG.info('Executing deployment logic ...')
        if self.stack_id is None:
            f = open(os.path.join(BUNDLE_DIR, 'data', 'aaa-deployment.yaml'))
            template = f.read()
            f.close()

            self.stack_id = self.deployer.deploy(template, self.token, parameters={'cms_dss_input':'8.8.8.8'}, name='AAAaaS_' + str(random.randint(1000, 9999)))
            LOG.info('Stack ID: ' + self.stack_id.__repr__())

    def provision(self, attributes):
        """
        (Optional) if not done during deployment - provision.
        """
        LOG.info('Executing resource provisioning logic...')
        if attributes:
            #print attributes
            if 'mcn.endpoint.dssaas' in attributes:
                self.dss_endpoint = str(attributes['mcn.endpoint.dssaas'])
            if 'mcn.endpoint.api' in attributes:
                self.dns_api = str(attributes['mcn.endpoint.api'])
                self.dnsaas = DnsaasClientAction(self.dns_api, token=self.token)

                LOG.info('DNS EP is: ' + self.dns_api )
            if 'mcn.endpoint.forwarder' in attributes:
                self.dns_forwarder = str(attributes['mcn.endpoint.forwarder'])
                LOG.info('DNS forwarder is: ' + self.dns_forwarder)

        # Update stack
        self.update(True)

        # if self.dns_api is not None:
        LOG.debug('Executing resource provisioning logic')
        # once logic executes, deploy phase is done
        self.ready_event.set()


    def dispose(self):
        """
        Dispose SICs.
        """
        LOG.info('Disposing of third party service instances...')
        if self.stack_id is not None:
            self.deployer.dispose(self.stack_id, self.token)
            self.stack_id = None
            #
            self.stop_event.set()

    def state(self):
        """
        Report on state.
        """
        if self.stack_id is not None:
            tmp = self.deployer.details(self.stack_id, self.token)
            LOG.info('Returning Stack output state...')
            output = ''
            try:
                output = tmp['output']
            except KeyError:
                pass
            return tmp['state'], self.stack_id, output
        else:
            LOG.info('Stack output: none - Unknown, N/A')
            return 'Unknown', 'N/A', None

    def update(self, provisioning = False, attributes = None):
        """
        Update SICs.
        """
        LOG.info('Executing update logic ...')

        if attributes:
            #print attributes
            if 'mcn.endpoint.dssaas' in attributes:
                self.dss_endpoint = str(attributes['mcn.endpoint.dssaas'])
            if 'mcn.endpoint.api' in attributes:
                self.dns_api = str(attributes['mcn.endpoint.api'])
                self.dnsaas = DnsaasClientAction(self.dns_api, token=self.token)

                LOG.info('DNS EP is: ' + self.dns_api )
            if 'mcn.endpoint.forwarder' in attributes:
                self.dns_forwarder = str(attributes['mcn.endpoint.forwarder'])
                LOG.info('DNS forwarder is: ' + self.dns_forwarder)
        # Wait for any pending operation to complete
        while (True):
            if self.stack_id is not None:
                tmp = self.deployer.details(self.stack_id, self.token)
                if tmp['state'] == 'CREATE_COMPLETE' or tmp['state'] == 'UPDATE_COMPLETE':
                    break
                else:
                    time.sleep(10)

        if self.stack_id is not None:
            f = open(os.path.join(BUNDLE_DIR, 'data', 'aaa-update.yaml'))
            template = f.read()
            f.close()

            self.deployer.update(self.stack_id, template, self.token, parameters={'cms_dss_input':self.dss_endpoint})
            LOG.info('Updated stack ID: ' + self.stack_id.__repr__())

    def notify(self, entity, attributes, extras):
        super(SOE, self).notify(entity, attributes, extras)

class SOD(service_orchestrator.Decision, threading.Thread):
    """
    Sample Decision part of SO.
    """

    def __init__(self, so_e, token, tenant, ready_event, stop_event):
        super(SOD, self).__init__(so_e, token, tenant)

        threading.Thread.__init__(self)
        self.ready_event = ready_event
        self.stop_event = stop_event
        self.time_wait = self.so_e.time_wait


    def run(self):
        """
        Decision part implementation goes here.
        """
        LOG.debug('AAAaaS SOD - Waiting for deploy and provisioning to finish')
        self.ready_event.wait()
        LOG.debug('AAAaaS SOD - Starting runtime logic...')


        # RUN-TIME MANAGEMENT
        while not self.stop_event.isSet():
            event_is_set = self.stop_event.wait(self.time_wait)

            if self.so_e.dns_info_configured is not True and self.so_e.dns_api is not None:
                res_Openam = False
                res_Profile = False
                state, stack_id, stack_output = self.so_e.state()
                if stack_output is not None:
                    for line in stack_output:
                        if line['output_key'] == 'mcn.endpoint.aaa-profile-instance':
                            self.so_e.recInfoProfile = str(line['output_value'])
                            res_Openam = self.perform_dnsconf(self.so_e.dnsaas, self.so_e.aaaDomainName, self.so_e.recProfile,
                                                              self.so_e.recInfoProfile)

                        if line['output_key'] == 'mcn.endpoint.aaa-openam-instance':
                            self.so_e.recInfoOpenam = str(line['output_value'])
                            res_Profile = self.perform_dnsconf(self.so_e.dnsaas, self.so_e.aaaDomainName, self.so_e.recOpenam,
                                                               self.so_e.recInfoOpenam)

                if res_Openam and res_Profile:
                    self.so_e.dns_info_configured = True
                    LOG.info('DNS information for AAA configured')
                    self.time_wait = self.so_e.time_wait_after_dns #wait more work is done


        if self.stop_event.isSet():
            LOG.debug('AAAaaS SOD - STOP event set after disposal')
            if self.so_e.dns_info_configured:
                res_Openam = self.remove_dnsconf(self.so_e.dnsaas, self.so_e.aaaDomainName, self.so_e.recProfile,
                                                              self.so_e.recInfoProfile)
                res_Profile = self.remove_dnsconf(self.so_e.dnsaas, self.so_e.aaaDomainName, self.so_e.recOpenam,
                                                               self.so_e.recInfoOpenam)

                if res_Openam and res_Profile:
                    self.so_e.dns_info_configured = True
                    LOG.info('DNS information remove successfully!')


    def perform_dnsconf(self, dnsaas, domain, record, info_rec, rec_type='A'):
        if dnsaas is not None:
            LOG.info('Created Record ' + record + ' domain=' + domain + ' info_rec=' + info_rec)
            lbDomainExists = dnsaas.get_domain(domain, self.so_e.token)
            if lbDomainExists.get('code', None) is not None and lbDomainExists['code'] == 404:
                resultDo = -1
                while (resultDo != 1):
                    time.sleep(2)
                    resultDo = dnsaas.create_domain(domain, "info@aaa-test.it", 3600, self.so_e.token)
                LOG.info('Domain created ' + domain)
            else:
                LOG.info('Domain Already Exists ' + domain)

            lbRecordExists = dnsaas.get_record(domain_name=domain, record_name=record, record_type=rec_type,
                                                           token=self.so_e.token)
            resultRe = -1
            if lbRecordExists.get('code', None) is not None and lbRecordExists['code'] == 404:
                while (resultRe != 1):
                    time.sleep(2)
                    resultRe = dnsaas.create_record(domain_name=domain,record_name=record, record_type=rec_type,
                                                                record_data=info_rec, token=self.so_e.token)
                LOG.info('Created Record ' + record + ' domain=' + domain + ' info_rec=' + info_rec)
            else:
                LOG.info('Record Already Exists will update to:' + record + ' domain=' + domain + ' info_rec=' + info_rec)
                while (resultRe != 1):
                    time.sleep(2)
                    resultRe = dnsaas.update_record(domain_name=domain,record_name=record, record_type=rec_type,
                                                    parameter_to_update='data', record_data=info_rec, token=self.so_e.token)
            return True
        else:
            LOG.info('Something wrong dnsaasclient not set!')
            return False


    def remove_dnsconf(self, dnsaas, domain, record, info_rec, rec_type='A'):
        if dnsaas is not None:
            LOG.info('Remove Record ' + record + ' domain=' + domain + ' info_rec=' + info_rec)
            result = -1
            while (result != 1):
                time.sleep(1)
                result = dnsaas.delete_record(domain, record, rec_type, self.token)
                try:
                    if result.get('status', None) is not None:
                        if(result['status'] == '404'):
                            break
                except:
                    break
            return True
        else:
            LOG.info('Something wrong dnsaasclient not set!')
            return False

    def stop(self):
        pass


class ServiceOrchestrator(object):
    """
    Sample SO.
    """
    def __init__(self, token, tenant):

        # this python thread event is used to notify the SOD that the runtime phase can execute its logic
        self.ready_event = threading.Event()
        # this python thread event is used to notify the SOD to stop runtime phase after a delete(and end the thread)
        self.stop_event = threading.Event()

        self.so_e = SOE(token, tenant, self.ready_event, self.stop_event)
        self.so_d = SOD(self.so_e, token, tenant, self.ready_event, self.stop_event)
        self.so_d.start()

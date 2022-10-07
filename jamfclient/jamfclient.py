import json
import requests
from requests.auth import HTTPBasicAuth
from typing import List


class JamfProClient:

    def __init__(self, username: str,
                 password: str,
                 base_url: str,
                 verify_cert: bool = True):

        self.base_url = f'https://{base_url}/api'
        self.username = username
        self.password = password
        self.session = requests.session()
        self.session.verify = verify_cert

    def authenticate(self) -> str:
        """
        Authenticate to Jamf Pro API using id and secret supplied on instantiation.
        """

        response = self.session.post(f'{self.base_url}/v1/auth/token',
                                     auth=HTTPBasicAuth(self.username,
                                                        self.password))

        if response.status_code == 200:
            headers = {'Authorization': f'Bearer {response.json()["token"]}'}

            self.session.headers = headers

        else:
            print('Authentication failed!')
            return 'Authentication failed!'

    def invalidate_token(self) -> bool:
        """
        Invalidate token obtained using the .authenticate() method.
        """

        response = self.session.post(f'{self.base_url}/v1/auth/invalidate-token')

        return response.status_code == 204

    def refresh_token(self) -> bool:
        """
        Invalidates current token and generates a new token.
        """

        response = self.session.post(f'{self.base_url}/v1/auth/keep-alive')

        if response.status_code == 200:
            headers = {'Authorization': f'Beaerer {response.json()["token"]}'}

            self.session.headers = headers

        else:
            print('Token refresh failed!')
            return 'Token refresh failed!'

    def get_auth_details(self) -> dict:
        """
        Retrieve authorization details associated with current token.
        """

        response = self.session.get(f'{self.base_url}/v1/auth')

        if response.status_code == 200:
            return response.json()
        else:
            print('Retrieval failed!')
            return {'Error': response.json()}

    def get_computer_groups(self) -> List:
        """
        Return a list of all computer groups.
        """

        response = self.session.get(f'{self.base_url}/v1/computer-groups')

        if response.status_code == 200:
            return response.json()
        else:
            print('Computer group retrieval failed!')
            return {'Error': 'Computer group retrieval failed!'}

    def get_computer_inventory(self, sections: List = None, page_size: int = 100,
                               sort: List = None, filter: str = None) -> List:
        """
        Returns List of computer inventory records.
        """

        page = 0
        params = {'page-size': page_size}
        params['sort'] = ','.join(sort) if sort else None
        params['sections'] = f'section={"&section=".join(sections)}' if sections else None

        response = self.session.get(f'{self.base_url}/v1/computers-inventory',
                                    params=params)

        if response.status_code == 200:
            results = response.json()['results']
            print(len(results))
            total = response.json()['totalCount']
            total_pages = (total//page_size)

            while page != total_pages:
                page += 1
                params['page'] = page
                response = self.session.get(f'{self.base_url}/v1/computers-inventory',
                                            params=params)

                if response.status_code == 200:
                    results += response.json()['results']
                    print(len(results))

                else:
                    print('Failed iteration')
                    return [{'Error': f'Failed iteration - {response.status_code}'}]

            return results

        else:
            print('Failed to retrieve records')
            return [{'Error': f'Failed to retrieve records - {response.status_code}'}]

    def get_computers(self, page_size: int = 100, sort: str = None) -> List:
        """
        Returns a list of computers.
        """

        page = 0
        params = {'page-size': page_size}

        params['sort'] = ','.join(sort) if sort else ''

        response = self.session.get(f'{self.base_url}/preview/computers',
                                    params=params)

        if response.status_code == 200:
            results = response.json()['results']
            print(len(results))
            total = response.json()['totalCount']
            total_pages = (total//page_size)

            while page != total_pages:
                page += 1
                params['page'] = page
                response = self.session.get(f'{self.base_url}/preview/computers',
                                            params=params)

                if response.status_code == 200:
                    results += response.json()['results']
                    print(len(results))

                else:
                    print('Failed iteration')
                    return [{'Error': f'Failed iteration - {response.status_code}'}]

            return results

        else:
            print('Failed to retrieve records')
            return [{'Error': f'Failed to retrieve records - {response.status_code}'}]

    def read_mdm_command(self, uuids: List = None, client_mgmt_id: str = None) -> List:
        """
        Get information about mdm commands made by Jamf Pro.
        """

        if uuids:
            params = {'uuids': uuids}
        elif client_mgmt_id:
            params = {'client-management-id': client_mgmt_id}
        else:
            print('No parameters specified!')
            return [{'Error': 'No parameters specified!'}]

        response = self.session.get(f'{self.base_url}/v1/mdm/commands', params=params)

        if response.status_code == 200:
            return response.json()
        else:
            print('Error retrieving mdm cmd!')
            return [{'Error': f'Error retrieving mdm cmd - {response.status_code}'}]

    def get_macos_updates(self) -> dict:
        """
        Retrieves available macOS managed software updates.
        """

        response = self.session.get(f'{self.base_url}/v1/macos-managed-software-updates/available-updates')

        if response.status_code == 200:
            return response.json()
        else:
            print('Error retrieving updates!')
            return {'Error': f'Error retrieving updates - {response.status_code}'}

    def push_macos_updates(self, max_deferrals: int, version: float, skip_version_verification: bool = False,
                           apply_major_update: bool = False, update_action: str = 'DOWNLOAD_AND_INSTALL',
                           force_restart: bool = False, device_ids: List = None, group_id: int = None):

        payload = {
            'maxDeferrals': max_deferrals,
            'version': version,
            'skipVersionVerfication': skip_version_verification,
            'applyMajorUpdate': apply_major_update,
            'updateAction': update_action,
            force_restart: force_restart
        }

        if device_ids:
            payload['deviceIds'] = device_ids
        elif group_id:
            payload['groupId'] = group_id
        else:
            print('Error: Please provide either device or group IDs!')
            return {'Error': 'No device/group IDs specified.'}

        response = self.session.post(f'{self.base_url}/v1/macos-managed-software-updates/send-updates')

        if response.status_code == 200:
            if response.json()['errors']:
                print('Updates sent with errors.')
                print(json.dumps(response.json()['errors'], indent=4))

            return response.json()
        else:
            print('Error sending updates!')
            return {'Error': f'Error sending updates - {response.status_code}'}


class JamfProtectClient:
    def __init__(self, username: str,
                 password: str,
                 base_url: str,
                 verify_cert: bool = True):

        self.username = username
        self.password = password
        self.base_url = base_url
        self.verify = verify_cert

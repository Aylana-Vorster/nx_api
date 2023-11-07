import requests, json
import time
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
#import file_manager
#file_settings = file_manager.file_manager()

class NX:
    def __init__(self, server, user, password):
        self.server = server
        self.user = user
        self.passw = password

    def get_headers(self): #Used to get the token and authentication headers for whicheever way of authenticating in the requests later
        nx_server_url = "https://{server}:7001/rest/v1/".format(server=self.server)
        login_payload = {'username':self.user, 'password':self.passw}
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        auth_token = requests.request("POST", nx_server_url + "login/sessions", headers=headers, data=login_payload, verify=False, timeout=15).json()["token"]
        headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
        return auth_token, headers
    
    def get_all_recording_devices(self): #Gets all active devices with their id, name, server ID if and only if a recording liscence is used on the came
        token, headers = self.get_headers()
        nx_server_url = "https://{server}:7001/rest/v1/".format(server=self.server)
        response = requests.get(nx_server_url + 'devices?_format=JSON&_with=id%2Curl%2Cname%2CserverId%2CisLicenseUsed%3DTrue', headers=headers, verify=False)
        return response.json()

    def get_video(self, guid, start_time): #Pull a video clip of 20 seconds from a device with limited resolution
        token, headers = self.get_headers()
        video_url = "https://" + self.server+":7001/media/"+guid+".webm?pos="+start_time+"&duration=20&accurate_seek&resolution=640x480&auth="+token
        return video_url

    def get_bookmark_event_link_guid(self): 
        #For each event rule, get the camera ID and the event ID where the tags are bookmark_open or deep_learning, the event rule is not disabled
        # and the type of event is to create a bookmark 
        token, headers = self.get_headers()
        nx_server_url = "https://{server}:7001/rest/v1/".format(server=self.server)
        response = requests.get(nx_server_url + "/ec2/getEventRules?format=json", headers=headers, verify=False,).json()
        for item in response:
            action_params = json.loads(item['actionParams'])
            action_resource_ids = item['actionResourceIds']  #the guid
            event_id = item['id']
            tags = action_params.get('tags', 'Tag not found')

        if (
            tags == 'bookmark_open'
            or tags == 'deep_learning'
            and item['actionType'] == 'bookmarkAction'
            and not item['disabled']
             ):
            rule_id = item['id'][1:-1]  # Removing curly braces
            action_resource_ids = action_resource_ids[0][1:-1]  # Removing curly braces

            simple_response = f"{rule_id}, {action_resource_ids}"
            return simple_response

    import json  

    def create_bookmark(self, creation_time, guid, caption, description): 
        #With a time delay, create a bookmark on a camera. This is typically used to make a bookmark after an event has been received, thus
        #there is a time shift on the creation and start time to get some pre-recording of an event. The whole bookmark is 15 seconds long
        time.sleep(2)
        token, headers = self.get_headers()
        start_time = int((creation_time * 1000) - 5000)
        creation_time_ms = int((creation_time * 1000) - 2000)

        body = {
            "name": caption,
            "description": description,
            "startTimeMs": start_time,
            "durationMs": 15000,
            "tags": [""],
            "creationTimeMs": creation_time_ms
        }

        nx_server_url = "https://{server}:7001/rest/v1/".format(server=self.server)
        endpoint_url = nx_server_url + 'devices/' + guid + '/bookmarks' 
 
        # Use requests.post for creating a new bookmark
        response = requests.post(endpoint_url, headers=headers, json=body, verify=False)
        
        # Print response details for debugging
        print("Response Code:", response.status_code)
        print("Response Text:", response.text)

        # Check if the request was successful
        if response.status_code == 200:
            return response.json()
        else:
            return None  


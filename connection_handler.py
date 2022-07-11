import requests
import json
import time


class ConnectionHandler:
    RPI_ADDR = "gui.local:80"
    PRESS_DEVICE_ID = 120

    def get_task(self):
        url = f"http://{self.RPI_ADDR}/task"
        r = requests.get(url=url)
        # data = r.json()
        
        return r.json() if r else None

    def get_stop_flag(self):
        url = f"http://{self.RPI_ADDR}/press/stop"
        r = requests.get(url=url)
        # data = r.json()
        
        return r.json() if r else None
    
    def post_values(self, values):
        url = f"http://{self.RPI_ADDR}/api/devices/{self.PRESS_DEVICE_ID}/add-values-by-property-id"
        headers = {
                "Content-type":"application/json", 
                "Accept":"text/plain"
                }
        data = json.dumps(values)
        response = requests.post(url=url, data=data, headers=headers)
        # print(response)
        return response.json() if response else None

    def patch_done_flag(self, job_id = -1, is_done = True): 
        url = f"http://{self.RPI_ADDR}/task/status"
        headers = {
                    "Content-type":"application/json", 
                    "Accept":"text/plain"
                   }   
        body = {
                "id": job_id,
                "done": is_done
                }
        data = json.dumps(body)
        print("data: ")
        print(data)
        response = requests.patch(url=url, headers=headers, data=data)
        print(response)

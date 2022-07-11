import requests
import json


class ConnectionHandler:
    RPI_ADDR = "51.158.163.165"
    PRESS_DEVICE_ID = 120

    def get_task(self):
        url = f"http://{self.RPI_ADDR}/api/device-jobs/device/{self.PRESS_DEVICE_ID}/false-done-flag"
        r = requests.get(url=url)
        # data = r.json()
        
        return r.json() if r else None

    def post_value(self, entity_name, property_id, value, job_id = 0):
        url = f"http://{self.RPI_ADDR}/api/devices/{self.PRESS_DEVICE_ID}/add-values-by-property-id"
        headers = {
                "Content-type":"application/json", 
                "Accept":"text/plain"
                }
        body = {
                "propertyId": property_id,
                "propertyName": entity_name,
                "deviceJobId": job_id,
                "val": str(value)
                }
        data = json.dumps(body)
        response = requests.post(url=url, data=data, headers=headers)
        # print(response)
        return response.json() if response else None

    def patch_done_flag(self, job_id, is_done = True): 
        url = f"http://{self.RPI_ADDR}/api/device-jobs/{job_id}/done-flag-value"
        headers = {
                    "Content-type":"application/json", 
                    "Accept":"text/plain"
                   }   
        body = {
                "done": is_done
                }
        data = json.dumps(body)
        response = requests.patch(url=url, headers=headers, data=data)
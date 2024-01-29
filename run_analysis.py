from formant_client import FormantClient
from env import *
import tqdm

from process_task_reports import process_task_reports

def main():
    fclient = FormantClient(
        admin_api_endpoint=API_ENDPOINT,
        formant_email=FORMANT_EMAIL,
        formant_password=FORMANT_PASSWORD,
    )
    
    # Get all robots
    robots = fclient.query_robots()
    robot_ids = [robot["id"] for robot in robots]

    # List of all task reports
    all_task_reports = []

    for robot in tqdm.tqdm(robot_ids, desc="Downloading task reports..."):
        task_reports = fclient.get_task_list_for_device_sync(robot)
        all_task_reports.extend(task_reports)

    process_task_reports(all_task_reports)

if __name__ == "__main__":
    main()
import json
import tqdm 

def process_task_reports(task_reports):

    total_run_count = 0
    redundancy_count = 0
    
    task_reports_x_cordinates = [t["report"]["robotCleaningSquareX"] for t in task_reports]
    task_reports_y_cordinates = [t["report"]["robotCleaningSquareY"] for t in task_reports]
    pairs = zip(task_reports_x_cordinates, task_reports_y_cordinates)

    


    for _ in tqdm.tqdm(task_reports, desc="Processing task reports..."):
        total_run_count += 1
        
        x = task_report["report"]["robotCleaningSquareX"]
        y = task_report["report"]["robotCleaningSquareY"]

        pairs.remove((x, y))

        if (x, y) in pairs:
            redundancy_count += 1

    print(f"Redundancy: {redundancy_count}")
    print(f"Total: {total_run_count}")
    print(f"Redundancy percentage: {round(redundancy_count / total_run_count * 100, 2)}%")

if __name__ == "__main__":
    import json
    with open("task_reports.json", "r") as f:
        all_task_reports = json.load(f)

    process_task_reports(all_task_reports)

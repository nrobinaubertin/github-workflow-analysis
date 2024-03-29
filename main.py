import json
import sys
from time import sleep

import requests
import postgres as db
import logs

SLEEP_TIMEOUT = 4

# Declare some run constants
with open("config.json", "r") as config_file:
    config = json.load(config_file)
    TOKEN = config["token"]
    OWNER = config["owner"]
    DB_NAME = config["db_name"]
    DB_DSN = config["db_dsn"]
    REPOSITORIES = config["repositories"]


def get_data_for_repo(db_dsn, repo):
    # Define the date one month ago
    # format datetime object as ISO 8601 string
    base_url = f"https://api.github.com/repos/{OWNER}/{repo}/actions/runs"
    headers = {"Authorization": f"token {TOKEN}"}

    conn = db.create_connection(db_dsn)

    if conn is None:
        print("Error! Cannot create the database connection.")

    print(f"Started scanning {repo}.")

    pages_without_new_stored_run = 0
    for page in range(15):
        new_stored_run = False
        print(f"page {page + 1}")
        url = base_url + "?" + "status=completed&per_page=100" + f"&page={page + 1}"
        response = requests.get(url, headers=headers, timeout=10)
        runs = response.json()
        if "workflow_runs" not in runs:
            print(runs)
            sys.exit("Something went wrong during the runs fetch")
        for run in runs["workflow_runs"]:
            if not db.run_exists(conn, run["id"]):
                run["logs"] = logs.fetch(run["logs_url"], conn, headers)
                store_run(conn, run)
                new_stored_run = True
                print(f"Stored run {run['run_number']}.")

                # query jobs
                if "jobs_url" in run:
                    sleep(SLEEP_TIMEOUT)
                    response = requests.get(
                        run["jobs_url"], headers=headers, timeout=10
                    )
                    jobs = response.json()
                    for job in jobs["jobs"]:
                        db.insert_job(conn, job)
                        for step in job["steps"]:
                            db.insert_step(conn, step, job["id"])
        if not new_stored_run:
            pages_without_new_stored_run += 1
        if pages_without_new_stored_run > 3:
            break
        sleep(SLEEP_TIMEOUT)

    print(f"Finished scanning {repo}.")


# remove NUL bytes that text fields cannot store (in PostgreSQL)
def clean_nul_bytes(value):
    if isinstance(value, dict):
        return {k: clean_nul_bytes(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [clean_nul_bytes(item) for item in value]
    elif isinstance(value, str):
        return value.replace("\x00", "")
    else:
        return value


def store_run(conn, data):
    data = clean_nul_bytes(data)
    db.insert_actor(
        conn,
        (
            data["actor"]["id"],
            data["actor"]["login"],
            data["actor"]["url"],
            data["actor"]["type"],
            data["actor"]["site_admin"],
        ),
    )
    db.insert_commit(
        conn,
        (
            data["head_commit"]["id"],
            data["head_commit"]["tree_id"],
            data["head_commit"]["message"],
            data["head_commit"]["timestamp"],
            data["head_commit"]["author"]["name"],
            data["head_commit"]["author"]["email"],
            data["head_commit"]["committer"]["name"],
            data["head_commit"]["committer"]["email"],
        ),
    )
    db.insert_repository(
        conn,
        (
            data["repository"]["id"],
            data["repository"]["name"],
            data["repository"]["full_name"],
            data["repository"]["private"],
            data["repository"]["owner"]["login"],
            data["repository"]["owner"]["id"],
            data["repository"]["url"],
            data["repository"]["owner"]["site_admin"],
            data["repository"]["html_url"],
            data["repository"]["description"],
            data["repository"]["fork"],
        ),
    )
    db.insert_run(
        conn,
        (
            data["id"],
            data["name"],
            data["head_branch"],
            data["head_sha"],
            data["path"],
            data["display_title"],
            data["run_number"],
            data["event"],
            data["status"],
            data["conclusion"],
            data["workflow_id"],
            data["check_suite_id"],
            data["url"],
            data["created_at"],
            data["updated_at"],
            data["run_attempt"],
            data["run_started_at"],
            data["workflow_url"],
            data["actor"]["id"],
            data["head_commit"]["id"],
            data["referenced_workflows"][0]["sha"]
            if len(data["referenced_workflows"])
            else "",
            data["repository"]["id"],
        ),
    )
    for name in data["logs"]:
        conn.execute(
            """
            INSERT INTO logs(run_id, log_identifier, log_content) VALUES(%s, %s, %s)
        """,
            (data["id"], name, data["logs"][name]),
        )


db.setup_database(DB_DSN)
for repo in REPOSITORIES:
    get_data_for_repo(DB_DSN, repo)

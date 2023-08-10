import requests
import zipfile
import io


def fetch(log_url, cursor, headers):
    logs = {}

    response = requests.get(log_url, headers=headers, timeout=10, stream=True)

    if response.status_code != requests.codes.ok:
        return logs

    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
        for info in zip_ref.infolist():
            with zip_ref.open(info.filename) as log_file:
                logs[info.filename] = log_file.read().decode("utf-8", "ignore")

    return logs

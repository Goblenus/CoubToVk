import requests
import argparse
import os
import datetime
import json
import time
import vk_requests
import traceback


def get_coubs_data(page=1, url="/api/v2/timeline/hot"):
    coubs_response = requests.get("http://coub.com" + url, params={"page": page})
    if coubs_response.status_code != 200:
        return []

    return coubs_response.json()


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-l', '--vk_login', type=str, required=True)
    parser.add_argument('-p', '--vk_password', type=str, required=True)
    parser.add_argument('-g', '--vk_group_id', type=int, required=True)
    parser.add_argument('-a', '--vk_application_id', type=str, required=True)
    parser.add_argument('-s', '--storage_folder', type=str, default="storage")
    parser.add_argument('-t', '--sleep_time', type=int, default=1800)
    parser.add_argument('-n', '--coub_upload_name', type=str, default="")
    parser.add_argument('-d', '--coub_upload_description', type=str, default="#coub")
    args = parser.parse_args()

    if not str(args.storage_folder).startswith("/"):
        args.storage_folder = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                                           args.storage_folder))

    if not os.path.exists(args.storage_folder):
        os.makedirs(args.storage_folder)
    elif os.path.exists(args.storage_folder) and os.path.isfile(args.storage_folder):
        return 1

    while True:
        try:
            current_storage_file_path = os.path.join(args.storage_folder,
                                                     datetime.datetime.utcnow().strftime("%Y-%m-%d.json"))
            yesterday_storage_file_path = os.path.join(args.storage_folder,
                                                       (datetime.datetime.utcnow() - datetime.timedelta(days=1))
                                                       .strftime("%Y-%m-%d.json"))

            current_storage = {"Coubs": []}
            yesterday_storage = {"Coubs": []}

            if os.path.exists(current_storage_file_path):
                with open(current_storage_file_path, encoding="utf-8") as current_storage_file:
                    current_storage = json.loads(current_storage_file.read())

            if os.path.exists(yesterday_storage_file_path):
                with open(yesterday_storage_file_path, encoding="utf-8") as yesterday_storage_file:
                    yesterday_storage = json.loads(yesterday_storage_file.read())

            total_pages = get_coubs_data()["total_pages"]

            new_coub_data = None

            for i in range(1, total_pages):
                coubs_data = get_coubs_data()

                for coub_data in coubs_data["coubs"]:
                    if (current_storage is not None and str(coub_data['permalink']) in current_storage["Coubs"]) \
                            or (yesterday_storage is not None
                                and str(coub_data['permalink']) in yesterday_storage["Coubs"]):
                        continue

                    new_coub_data = coub_data
                    break

                if new_coub_data is not None:
                    break

            if new_coub_data is None:
                continue

            vk_api = vk_requests.create_api(app_id=args.vk_application_id, login=args.vk_login,
                                            password=args.vk_password,
                                            scope=['offline', 'groups', 'video', 'messages', 'wall'])

            response = vk_api.video.save(name=args.coub_upload_name, description=args.coub_upload_description,
                                         wallpost=1, link="http://coub.com/view/{}".format(new_coub_data['permalink']),
                                         group_id=args.vk_group_id)

            requests.get(response['upload_url'])

            current_storage["Coubs"].append(new_coub_data['permalink'])

            with open(current_storage_file_path, "w") as current_storage_file:
                current_storage_file.write(json.dumps(current_storage))
        except Exception as e:
            print("{}".format(str(traceback.print_exc())))
        finally:
            time.sleep(args.sleep_time)

if __name__ == "__main__":
    exit(main())
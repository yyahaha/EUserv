import os
import json
import time
import requests
from bs4 import BeautifulSoup

USERNAME = os.environ["USERNAME"]
PASSWORD = os.environ["PASSWORD"]
SERVERS = {}
PROXIES = {
    "http": "http://127.0.0.1:10809",
    "https": "http://127.0.0.1:10809"
}


def login() -> requests.session:
    global PROXIES, USERNAME, PASSWORD
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/83.0.4103.116 Safari/537.36",
        "origin": "https://www.euserv.com"
    }
    login_data = {
        "email": USERNAME,
        "password": PASSWORD,
        "form_selected_language": "en",
        "Submit": "Login",
        "subaction": "login"
    }
    url = "https://support.euserv.com/index.iphp"
    session = requests.Session()
    f = session.post(url, headers=headers, data=login_data)
    f.raise_for_status()
    if f.text.find('Hello') == -1:
        print("Login Failed! Please check your login details")
        exit(1)
    # print(f.request.url)
    sess_id = f.request.url[f.request.url.index('=') + 1:len(f.request.url)]
    return sess_id, session


def get_servers(sess_id, session):
    global SERVERS
    url = "https://support.euserv.com/index.iphp?sess_id=" + sess_id
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/83.0.4103.116 Safari/537.36",
        "origin": "https://www.euserv.com"
    }
    f = session.get(url=url, headers=headers)
    f.raise_for_status()
    soup = BeautifulSoup(f.text, 'html.parser')
    for tr in soup.select('#kc2_order_customer_orders_tab_content_1 .kc2_order_table.kc2_content_table tr'):
        server_id = tr.select('.td-z1-sp1-kc')
        if not len(server_id) == 1:
            continue
        flag = True if tr.select('.kc2_order_action_container .kc2_order_extend_contract_term_container')[
                           0].get_text().find('Contract extension possible from') == -1 else False
        SERVERS[server_id[0].get_text()] = flag


def renew(sess_id, session, order_id) -> bool:
    url = "https://support.euserv.com/index.iphp"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/83.0.4103.116 Safari/537.36",
        "origin": "https://www.euserv.com",
        "Referer": "https://support.euserv.com/index.iphp?sess_id="
                   + sess_id
                   + "&subaction=choose_order"
                   + "&choose_order_subaction"
                   + "=show_contract_details&ord_no="
                   + order_id
    }
    data = {
        "sess_id": sess_id,
        "subaction": "kc2_security_password_get_token",
        "prefix": "kc2_customer_contract_details_extend_contract_",
        "password": PASSWORD
    }
    f = session.post(url, headers=headers, data=data)
    f.raise_for_status()
    # print(f.text)
    token = json.loads(f.text)["token"]["value"]
    if not json.loads(f.text)["rs"] == "success":
        return False
    data = {
        "sess_id": sess_id,
        "ord_id": order_id,
        "subaction": "kc2_customer_contract_details_extend_contract_term",
        "token": token
    }
    session.post(url, headers=headers, data=data)
    time.sleep(5)
    return True


def check(sess_id, session):
    get_servers(sess_id, session)
    flag = True
    for key, val in SERVERS.items():
        if val:
            flag = False
            print("ServerID: %s Renew Error! Please Check" % key)
    if flag:
        print("ALL Work Done! Enjoy")


if __name__ == "__main__":
    sessid, s = login()
    get_servers(sessid, s)
    for k, v in SERVERS.items():
        if v:
            if not renew(sessid, s, k):
                print("ServerID: %s Renew Error! Please Check" % k)
    check(sessid, s)

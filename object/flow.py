import os
import json
import pandas as pd
import base64
import requests
import csv
import argparse
import logging
import configparser
import sys

BASEDIR = os.path.dirname(os.path.realpath('__file__'))


def __get_local_ips_from_config_csv(config_csv):
    private_ips = []
    with open(config_csv, 'r') as f:
        reader = csv.reader(f)
        csv_lines = list(reader)
        csv_lines.pop(0)
        for line in csv_lines:
            private_ips.append(line[0])
    mongo_connection_uri = 'mongodb://'
    for ip in private_ips:
        mongo_connection_uri = mongo_connection_uri + ip + ':27017,'
    mongo_connection_uri = mongo_connection_uri[:-1] + '/?replicaSet=RSEQ'
    # print(mongo_connection_uri)
    return private_ips, mongo_connection_uri


def get_master_node(host_ips):
    try:
        for ip in host_ips:
            url = "http://{}:9001/api/v1/core/tenant".format(ip)
            payload = {}
            headers = {
                'Authorization': 'Basic {}'.format(authorizationBase64)
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            if response.status_code == 200:
                return ip
    except Exception as e:
        print(str(e))


def get_authorizationBase64(Admin_UserName, Admin_Password):
    userpass = Admin_UserName + ":" + Admin_Password
    authorizationBase64 = base64.b64encode(userpass.encode("ascii")).decode("ascii")
    return authorizationBase64


def call_equalum_api(request_type, payload, master_ip, endpoint):
    url = "http://{}:9001/api/v1/core/{}".format(master_ip, endpoint)
    headers = {
        'Authorization': 'Basic {}'.format(authorizationBase64),
        'Content-Type': "application/json"
    }
    try:
        error = ''
        response_json = ''
        response = requests.request(request_type, url, headers=headers, data=payload)
        if response.content == b'OK':
            response_json = '{}'
        # elif response.status_code == 200:
        else:
            response_json = response.json()

        if request_type == 'GET' and response.status_code != 200:
            error = 'response status code is: ' + str(response.status_code)
        if request_type == 'POST' and not (response.status_code == 200 or response.status_code == 201):
            error = str(response_json['message'])
        status_code = response.status_code
        return response_json, status_code, error
    except Exception as e:
        print(error)
        raise
        
def build_flow_body(master_ip, flow_id, flow_name, tenant_id, tenant_name, targettenant_name):
        config = configparser.ConfigParser()
        config.read('Equalum_Object.ini')
        payload = {}
        if tenant_id == '0':
            payload = json.loads(config['FLOWS']['ENTRY'])
            payload['flowExport']['flow']['id'] = flow_id
            payload['flowExport']['flow']['name'] = flow_name
            payload['flowExport']['flow']['tenantId'] = tenant_id
            payload['flowExport']['tenantName'] = tenant_name
            payload['targetTenantName'] = targettenant_name
            payload = json.dumps(payload)
            print(payload)
        if payload != '{}':
            response_json, status_code, error = call_equalum_api('POST', payload, master_ip, 'flows/import')
        if status_code == 200:
            msg = 'Flow - {} with name - {} was created successfully'.format(flow_id, flow_name)
            print(msg)
            logging.info(msg)
        else:
            print(error)
            logging.info(error)

def get_flow_definition(master_ip):
    logging.info('Creating Objects')
    flow_id = str(sys.argv[1])
    flow_name = str(sys.argv[2])
    tenant_id = str(sys.argv[3])
    tenant_name = str(sys.argv[4])
    targettenant_name = str(sys.argv[5])
    print(flow_id)
    msg = '''Creating flow - {} with name - {}'''.format(flow_id, flow_name)
    print(msg)
    logging.info(msg)
    build_flow_body(master_ip, flow_id, flow_name, tenant_id, tenant_name, targettenant_name)


def main():
    logging.basicConfig(filename='object_creation.log', filemode='w', format='%(asctime)s - %(message)s',
                        level=logging.INFO)
    logging.info('\nStarting execution....')
    global authorizationBase64, mongo_connection_uri, machine_count
    Admin_UserName = str(sys.argv[6])
    Admin_Password = str(sys.argv[7])
    print(Admin_UserName)

    authorizationBase64 = get_authorizationBase64(Admin_UserName, Admin_Password)
    master_ip ='dev.equalum.gsk.com'
    print('Connected to Engine Master Ip: ', master_ip)
    logging.info('Connected to Engine Master Ip: ' + master_ip)
    get_flow_definition(master_ip)


if __name__ == "__main__":
        main()

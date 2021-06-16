import os
import json
import pandas as pd
import base64
import requests
import csv
import argparse
import logging
import configparser

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


def build_source_body(master_ip, source_type, source_name, user, password, host_servers):
    try:
        config = configparser.ConfigParser()
        config.read('Equalum_Object.ini')
        payload = {}
        if source_type == 'sqlServer':
            payload = json.loads(config['SOURCE']['SQL_SERVER'])
            payload['dataSource']['name'] = source_name
            payload['dataSource']['user'] = user
            payload['dataSource']['password'] = password
            payload['dataSource']['host'] = host_servers
            payload = json.dumps(payload)
            # print(payload)
        elif source_type == 'kafka':
            payload = json.loads(config['SOURCE']['KAFKA'])
            payload['dataSource']['name'] = source_name
            payload['dataSource']['servers'] = host_servers
            payload = json.dumps(payload)

        if payload != '{}':
            response_json, status_code, error = call_equalum_api('POST', payload, master_ip, 'sources')
        if status_code == 201:
            msg = 'Source of type - {} with name - {} was created successfully'.format(source_type, source_name)
            print(msg)
            logging.info(msg)
        else:
            print(error)
            logging.info(error)
    except Exception as e:
        print(e)
        logging.info(e)


def build_target_body(master_ip, target_type, target_name, user, password, host_servers, database_name, schema_name):
    try:
        config = configparser.ConfigParser()
        config.read('Equalum_Object.ini')
        payload = {}
        if target_type == 'sqlServerTarget':
            payload = json.loads(config['TARGET']['SQL_SERVER'])
            payload['targetName'] = target_name
            payload['user'] = user
            payload['password'] = password
            payload['host'] = host_servers
            payload['database'] = database_name
            payload['schema'] = schema_name
            payload = json.dumps(payload)
        # print(payload)
        elif target_type == 'kafkaTarget':
            payload = json.loads(config['TARGET']['KAFKA'])
            payload['targetName'] = target_name
            payload['brokerList'] = host_servers
            payload = json.dumps(payload)

        if payload != '{}':
            response_json, status_code, error = call_equalum_api('POST', payload, master_ip, 'targets')
        if status_code == 201:
            msg = 'Target of type - {} with name - {} was created successfully'.format(target_type, target_name)
            print(msg)
            logging.info(msg)
        else:
            print(error)
            logging.info(error)
    except Exception as e:
        print(e)
        logging.info(e)


def build_stream_body(master_ip, stream_type, stream_name, schema, table, topic, sourceid):
    try:
        config = configparser.ConfigParser()
        config.read('Equalum_Object.ini')
        payload = {}
        if stream_type == 'oracle':
            payload = json.loads(config['STREAM']['ORACLE'])
            payload['stream']['name'] = stream_name
            payload['stream']['schema'] = schema
            payload['stream']['table'] = table
            payload['topic']['topicType'] = topic
            payload = json.dumps(payload)
        # print(payload)
        elif stream_type == 'kafka':
            payload = json.loads(config['STREAM']['KAFKA'])
            payload['stream']['name'] = stream_name
            payload['stream']['schema'] = schema
            payload = json.dumps(payload)

        if payload != '{}':
            response_json, status_code, error = call_equalum_api('POST', payload, master_ip, 'sources/' + sourceid + '/create-stream')
        if status_code == 201:
            msg = 'Stream of type - {} with name - {} was created successfully'.format(stream_type, stream_name)
            print(msg)
            logging.info(msg)
        else:
            print(error)
            logging.info(error)
    except Exception as e:
        print(e)
        logging.info(e)


def build_flow_body(master_ip, flow_id, flow_name, tenant_id, tenant_name, targettenant_name):
    try:
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
    except Exception as e:
        print(e)
        logging.info(e)


def get_source_definition(master_ip, Objects_list):
    df = pd.read_csv(Objects_list)
    logging.info('Creating Sources')
    for index, row in df.iterrows():
        source_type = df['source_type'][index]
        source_name = df['source_name'][index]
        user = df['user'][index]
        password = df['password'][index]
        host_servers = df['host_servers'][index]

        msg = '''Creating Source of type - {} with name - {}'''.format(source_type, source_name)
        print(msg)
        logging.info(msg)
        build_source_body(master_ip, source_type, source_name, user, password, host_servers)


def get_target_definition(master_ip, Objects_list):
    df = pd.read_csv(Objects_list)
    logging.info('Creating Targets')
    for index, row in df.iterrows():
        target_type = df['target_type'][index]
        target_name = df['target_name'][index]
        database_name = df['database_name'][index]
        schema_name = df['schema_name'][index]
        user = df['user'][index]
        password = df['password'][index]
        host_servers = df['host_servers'][index]

        msg = '''Creating Target of type - {} with name - {}'''.format(target_type, target_name)
        print(msg)
        logging.info(msg)
        build_target_body(master_ip, target_type, target_name, user, password, host_servers, database_name, schema_name)


def get_stream_definition(master_ip, Objects_list):
    df = pd.read_csv(Objects_list, dtype=str)
    logging.info('Creating Streams')
    for index, row in df.iterrows():
        # sourceId = 1379
        sourceid = str(df['sourceId'][index])
        stream_type = df['stream_type'][index]
        stream_name = df['stream_name'][index]
        schema = df['schema'][index]
        table = df['table'][index]
        topic = df['topic'][index]

    msg = '''Creating Stream of type - {} with name - {}'''.format(stream_type, stream_name)
    print(msg)
    logging.info(msg)
    build_stream_body(master_ip, stream_type, stream_name, schema, table, topic, sourceid)


def get_flow_definition(master_ip, Objects_list):
    df = pd.read_csv(Objects_list, dtype=str)
    logging.info('Creating Flows')
    for index, row in df.iterrows():
        flow_id = str(df['flow_id'][index])
        tenant_id = str(df['tenant_id'][index])
        flow_name = df['flow_name'][index]
        tenant_name = df['tenant_name'][index]
        targettenant_name = df['targettenant_name'][index]
    msg = '''Creating flow - {} with name - {}'''.format(flow_id, flow_name)
    print(msg)
    logging.info(msg)
    build_flow_body(master_ip, flow_id, flow_name, tenant_id, tenant_name, targettenant_name)


def add_tenant(tenant_name, master_ip):
    payload = {
        "tenantName": ""
    }
    payload = json.loads(json.dumps(payload))
    payload['tenantName'] = tenant_name
    payload = json.dumps(payload)

    response_json, status_code, error = call_equalum_api('POST', payload, master_ip, 'tenant')
    if status_code == 201:
        msg = 'Tenant, {} was created successfully'.format(tenant_name)
        print(msg)
        logging.info(msg)
    else:
        msg = 'Tenant ' + tenant_name + ' was created successfully'
        print(msg)
        logging.info(msg)


def add_user(master_ip, user, new_user_pass):
    config = configparser.ConfigParser()
    config.read('Equalum_Object.ini')
    payload = {}
    payload = json.loads(config['USER']['USER'])
    default_permission = json.loads(config['USER']['DEFAULT_PERMISSION'])

    default_full_name = ''
    default_department = ''
    default_email = ''

    user_detail = user.split('&')
    user_name = user_detail[0]
    # print('*********************** ' + user_name + ' ************************')
    try:
        full_name = user_detail[1]
    except IndexError:
        full_name = default_full_name
    try:
        department = user_detail[2]
    except IndexError:
        department = default_department
    try:
        email = user_detail[3]
    except IndexError:
        email = default_email
    try:
        permission = user_detail[4]
        permission = json.loads(permission)
    except IndexError:
        permission = default_permission

    payload['userDetails']['username'] = user_name
    payload['userDetails']['password'] = new_user_pass
    payload['userDetails']['fullName'] = full_name
    payload['userDetails']['department'] = department
    payload['userDetails']['email'] = email
    payload['permissions'] = permission
    payload = json.dumps(payload)

    response_json, status_code, error = call_equalum_api('POST', payload, master_ip, 'user')
    if status_code == 201:
        msg = 'User, {} was created successfully'.format(user_name)
        print(msg)
        logging.info(msg)
    else:
        msg = 'User, ' + user_name + ' was created successfully'
        print(msg)
        logging.info(msg)


def main():
    logging.basicConfig(filename='object_creation.log', filemode='w', format='%(asctime)s - %(message)s',
                        level=logging.INFO)
    logging.info('\nStarting execution....')
    global authorizationBase64, mongo_connection_uri, machine_count

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", help="Location of CSV source list definition",
                        default='Sources.csv')
    parser.add_argument("--user", "-u", help="Equalum Username to be used", default='equalum', nargs='?')
    parser.add_argument("--password", "-p", help="Equalum Password to be used", default='GSK@equalum')
    parser.add_argument("--config_csv", "-c", help="Equalum Configuration file",
                        default='/eq/equalum/engine/conf/config.csv')
    parser.add_argument("--operation", "-o", help="Create Tenant / User / Source / Target / Stream / Flow",
                        required=True)
    parser.add_argument("--tenant", "-t", help="Tenant name to be created")
    parser.add_argument("--list_users", "-lu", help="List Users to be created")
    parser.add_argument("--user_password", "-up", help="New user password", default='Equalum')
    args = parser.parse_args()

    Admin_UserName = args.user
    Admin_Password = args.password
    Objects_list = args.file
    config_csv = args.config_csv
    operation = args.operation
    tenant_name = args.tenant
    list_users = args.list_users
    new_user_pass = args.user_password

    authorizationBase64 = get_authorizationBase64(Admin_UserName, Admin_Password)

    # host_ips, mongo_connection_uri = __get_local_ips_from_config_csv(config_csv)
    # master_ip = get_master_node(host_ips)

    master_ip = 'dev.equalum.gsk.com'

    print('Connected to Engine Master Ip: ', master_ip)
    logging.info('Connected to Engine Master Ip: ' + master_ip)

    if operation == 'Source':
        get_source_definition(master_ip, Objects_list)
    elif operation == 'Target':
        get_target_definition(master_ip, Objects_list)
    elif operation == 'Stream':
        get_stream_definition(master_ip, Objects_list)
    elif operation == 'Flow':
        get_flow_definition(master_ip, Objects_list)

    elif operation == 'Tenant':
        msg = 'Creating Tenant with name - {}'''.format(tenant_name)
        print(msg)
        logging.info(msg)
        add_tenant(tenant_name, master_ip)
    elif operation == 'User':
        users = list_users.split('||')
        msg = 'Creating Users'''
        print(msg)
        logging.info(msg)
        for user in users:
            user_detail = user.split('&')
            user_name = user_detail[0]
            msg = 'Creating User {}'''.format(user_name)
            print(msg)
            logging.info(msg)
            add_user(master_ip, user, new_user_pass)


if __name__ == "__main__":
    main()

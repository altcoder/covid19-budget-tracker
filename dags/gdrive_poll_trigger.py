import logging
import json
import requests
import os
from datetime import datetime, timedelta
import airflow
from airflow import DAG
from airflow.configuration import conf
from airflow.models import Variable
from airflow.utils.dates import days_ago
from airflow.operators.python_operator import BranchPythonOperator
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.operators.dummy_operator import DummyOperator
from lib_google_api import GoogleAPI

DAGS_DIR = conf.get('core', 'dags_folder')
CREDENTIALS_DIR = os.path.abspath(DAGS_DIR + "/../credentials") + '/'

with open( DAGS_DIR + "/../config/notebooks.json", 'r') as f:
    notebooks = json.load(f)

gapi = GoogleAPI(CREDENTIALS_DIR)

args = {
    'owner': 'altcoder',
    'start_date': datetime(2020, 3, 28),
    'catchup_by_default': False
}

def get_last_modified(**kwargs):
    gdrive = gapi.gdrive()

    name = kwargs.get('name')
    keyword = kwargs.get('keyword')
    mime_type = kwargs.get('mime_type')

    execution_time = kwargs.get('ts')
    start_time = datetime.strptime(execution_time, '%Y-%m-%dT%H:%M:%S%z')
    start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%S')
    logging.info('Fetching latest modified from %s' % start_time_str)
    # Google API Docs: https://developers.google.com/drive/api/v3/reference/files#resource
    results = gdrive.files().list(q="(name contains '%s') and (modifiedTime > '%s') and (mimeType = '%s')" % (keyword, start_time_str, mime_type),
                                spaces='drive',
                                pageSize=100,
                                fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime)").execute()

    items = results.get('files', [])
    for f in items:
        logging.info('MATCH! [%s] %s' % (f['createdTime'], f['name']))

    if len(items) > 0:
        logging.info('New data available. Running %s.' % name.lower())
        return f"trigger_{name.lower()}"
    else:
        return "stop"

dag = DAG(
    dag_id='gdrive_poll_trigger',
    default_args=args,
    schedule_interval="@hourly",
    catchup=False
)

with dag:

    stop_op = DummyOperator(task_id='stop', trigger_rule='all_done', dag=dag)

    start_op = DummyOperator(task_id='start', dag=dag)

    gdrive_triggers = ((name, attr) for name, attr in notebooks.items() if attr['type'] == 'gdrive')

    for name, attr in gdrive_triggers:
        check_gdrive_op = BranchPythonOperator (
            task_id=f'check_modified_{name.lower()}',
            python_callable=get_last_modified,
            provide_context=True,
            op_kwargs={"name": name, "keyword": attr['keyword'], "mime_type": attr['mime_type']},
            trigger_rule="all_done",
            dag=dag,
        )

        trigger_notebook_op = TriggerDagRunOperator(
            task_id=f"trigger_{name.lower()}",
            trigger_dag_id=name,
            dag=dag
        )

        start_op >> check_gdrive_op
        check_gdrive_op >> trigger_notebook_op
        check_gdrive_op >> stop_op
        trigger_notebook_op >> stop_op

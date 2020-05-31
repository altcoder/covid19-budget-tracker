import os
import glob
import json
import logging
import gzip
import tarfile
import shutil
from csv import reader as csv_reader
import papermill as pm
from datetime import datetime, timedelta

import airflow
from airflow import DAG
from airflow.configuration import conf
from airflow.utils.dates import days_ago
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.models import Variable

from lib_google_api import GoogleAPI

DAGS_DIR = conf.get('core', 'dags_folder')
NOTEBOOKS_DIR = os.path.abspath(DAGS_DIR + "/../notebooks") + '/' # Add '/' at the end because os.path.abspath() will remove it
OUTPUT_DIR = os.path.abspath(DAGS_DIR + "/../output") + '/'
CONFIG_DIR = os.path.abspath(DAGS_DIR + "/../config") + '/'
CREDENTIALS_DIR = os.path.abspath(DAGS_DIR + "/../credentials") + '/'

with open( CONFIG_DIR + "/notebooks.json", 'r') as f:
    notebooks = json.load(f)

gapi = GoogleAPI(CREDENTIALS_DIR)

def create_dag(dag_id, args):

    # notebook name without extension
    basename = args.get('basename')

    # notebook file, this will be executed
    notebook_file = NOTEBOOKS_DIR + basename + ".ipynb"

    # directory to look for output files
    output_root = OUTPUT_DIR

    dag = DAG(
        dag_id=dag_id,
        default_args=args,
        max_active_runs=1,
        schedule_interval=notebooks[basename]['interval'],
        dagrun_timeout=timedelta(minutes=60)
    )

    with dag:
        start = DummyOperator(task_id='start')
        stop = DummyOperator(task_id='stop')

        def clean_generated_files(**kwargs):
            for output_file in glob.glob(OUTPUT_DIR + '*'):
                if os.path.exists(output_file):
                    os.remove(output_file)

        def execute_notebook(**kwargs):
            name = kwargs.get('name')
            keyword = kwargs.get('keyword')
            mime_type = kwargs.get('mime_type')
            execution_time_str = kwargs.get('ts')
            try:
                # This is the format in production environment
                execution_time = datetime.strptime(execution_time_str, '%Y-%m-%dT%H:%M:%S.%f%z')
            except ValueError:
                execution_time = datetime.strptime(execution_time_str, '%Y-%m-%dT%H:%M:%S%z')
            execution_date_str = execution_time.strftime('%Y-%m-%d')

            pm.execute_notebook(
                input_path=notebook_file,
                output_path='/dev/null',
                parameters=dict({
                    'output_dir': OUTPUT_DIR,
                    'execution_date': execution_date_str,
                    'execution_time': execution_time_str,
                }),
                log_output=True,
                report_mode=True
            )

        def upload_gdrive_overwrite(path_to_file, file_name, mime_type, parent_dir_id):
            gapi.delete_gdrive_file(file_name, mime_type)
            gfile = gapi.upload_gdrive_file(path_to_file, file_name, mime_type, parent_dir_id)
            logging.info('Upload file "%s" successful with file ID: %s' % (file_name, gfile.get('id')))

        def upload_gdrive_compressed_file(path_to_file, file_name, parent_dir_id):
            gz_file = path_to_file + '.gz'
            with open(path_to_file, 'rb') as csv:
                with gzip.open(gz_file, 'wb') as gz:
                    shutil.copyfileobj(csv, gz)
            upload_gdrive_overwrite(gz_file, file_name, 'application/gzip', parent_dir_id)

        def upload_gdrive_compressed_files(glob_string, file_name, parent_dir_id):
            with tarfile.open(file_name, "w:gz") as tar:
                for file_match in glob.glob(glob_string):
                    tar.add(file_match, os.path.basename(file_match))
            upload_gdrive_overwrite(file_name, file_name, 'application/gzip', parent_dir_id)

        def upload_gsheet_csv(path_to_csv, sheet_id, sheet_range):
            with open(path_to_csv, 'r') as csv:
                #csv_contents = csv.read()
                reader = csv_reader(csv)
                csv_contents = list(reader)
            gsheet = gapi.update_gsheet_values(sheet_id, sheet_range, csv_contents)
            logging.info('Upload csv "%s" successful with file ID: %s' % (path_to_csv, gsheet))

        def post_process(**kwargs):
            posts = notebooks[basename]['posts']
            for post in posts:
                post_glob = OUTPUT_DIR + post['glob']
                post_process = post['process']
                if post_process == 'upload_gdrive_compressed_files':
                    upload_gdrive_compressed_files(post_glob, post['file_name'], post['parent_dir_id'])
                else:
                    for post_file in glob.glob(post_glob):
                        if os.path.exists(post_file):
                            logging.info('Processing: %s with %s' % (post_file, post_process))
                            if post_process == 'upload_gdrive_overwrite':
                                upload_gdrive_overwrite(post['path_to_file'], post['file_name'], post['mime_type'], post['parent_dir_id'])
                            elif post_process == 'upload_gdrive_compressed_file':
                                upload_gdrive_compressed_file(post_file, post['file_name'], post['parent_dir_id'])
                            elif post_process == 'upload_gsheet_csv':
                                upload_gsheet_csv(post_file, post['sheet_id'], post['sheet_range'])
                            else:
                                raise RuntimeError('Unsupported post processing %s' % post_process)

                    
        def create_dynamic_task(task_id, callable_function):
            task = PythonOperator(
                task_id=task_id,
                python_callable=callable_function,
                provide_context=True
            )
            return task

        cleanup = create_dynamic_task('cleanup', clean_generated_files)

        execute = create_dynamic_task('execute', execute_notebook)

        post_process = create_dynamic_task('post_process', post_process)

        start >> cleanup >> execute >> post_process >> stop

    return dag

#  Look for python notebooks to execute
for file in os.listdir(NOTEBOOKS_DIR):
    if file.startswith("."):
        continue
    filename_without_extension = os.path.splitext(file)[0]
    dag_id = filename_without_extension

    default_args = {'owner': 'altcoder',
                    'start_date': days_ago(2),
                    'basename': filename_without_extension
                    }
    globals()[dag_id] = create_dag(dag_id, default_args)

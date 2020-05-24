# Local Development

1. Clone this repo.

```
$ git clone https://github.com/altcoder/covid19-budget-tracker.git
$ cd covid19-budget-tracker
```

2. Install Docker (skip if already installed)

3. Setup Airflow variables

**config/airflow-vars.json** contains airflow variables that you would need in
order to  upload the output csv files to Google Sheet, AWS S3 and/or Snowflake.
These are optional. Recommended if you have your own storage. Make sure to look at
`dags/notebook_dags.py` on how to use it. 
```
$ cp config/airflow-vars-sample.json config/airflow-vars.json
[edit airflow-vars.json]
```

4. Start Airflow container (SequentialExecitor)
```
$ scripts/airflow.sh start
```

5. View Airflow container logs (optional)
```
$ scripts/airflow.sh logs
```

6. List Airflow DAGs (testing) 
```
$ scripts/airflow.sh list_dags

-------------------------------------------------------------------
DAGS
-------------------------------------------------------------------
...
github_poll_trigger
...

```
5. Test a DAG task
```
$ scripts/airflow.sh test github_poll_trigger check_commits_hello_world 2020-03-28
```

6. Start coding
```
$ jupyter-lab
```

7. (Optional) Setup virtualenv or Conda environment
```
$ conda create --prefix ./.${PWD##*/}
$ conda activate ./.${PWD##*/}
$ pip install -r requirements.txt
```

# Integration Test

1. Start Airflow container (SequentialExecitor)
```
$ scripts/airflow.sh start
```

2. Unpause dags 
```
$ scripts/airflow.sh unpause github_poll_trigger
$ scripts/airflow.sh unpause hello_world
```

3. Trigger dag 
```
$ scripts/airflow.sh trigger_dag -e 2020-03-28 github_poll_trigger
```

# Production Deployment

1. Publish to Dockerhub
```
$ scripts/airflow.sh build
$ scripts/airflow.sh publish
```

2. For LocalExecutor:
```
$ scripts/airflow.sh exec_local_up
...
$ scripts/airflow.sh exec_local_down
```

3. For CeleryExecutor:
```
$ scripts/airflow.sh exec_celery_up
...
$ scripts/airflow.sh exec_celery_down
```

4. For Astronomer:

```
$ astro dev init
$ astro dev start
$ astro deploy
```
5. Setup authentication

Modify config/airflow-prod.cfg  
```
[webserver]
...
authenticate = True
auth_backend = airflow.contrib.auth.backends.password_auth
```
Generate fernet_key using  
```
echo $(python -c "from cryptography.fernet import Fernet; FERNET_KEY = Fernet.generate_key().decode(); print(FERNET_KEY)")
```
Replace `fernet_key` in config/airflow-prod.cfg  
```
[core]
fernet_key = <YOUR_FERNET_KEY>
```
And in `scripts/docker-entrypoint.sh`
```
: "${AIRFLOW__CORE__FERNET_KEY:="<YOUR_FERNET_KEY>"}"
```
Generate user following [this
instructions](https://airflow.apache.org/docs/1.10.1/security.html)
```
# navigate to the airflow installation directory
$ cd ~/airflow
$ python
>>> import airflow
>>> from airflow import models, settings
>>> from airflow.contrib.auth.backends.password_auth import PasswordUser
>>> user = PasswordUser(models.User())
>>> user.username = 'new_user_name'
>>> user.email = 'new_user_email@example.com'
>>> user.password = 'set_the_password'
>>> session = settings.Session()
>>> session.add(user)
>>> session.commit()
>>> session.close()
>>> exit()
```

# Customizing Docker Image

You may want to rebuild the docker image when changes have been made to the
following files:
- requirements.txt
- scripts/docker-entrypoint.sh
- config/airflow.cfg
- Dockerfile

1.  Build image
```
$ docker build --rm -t altcoder/docker-airflow .
```


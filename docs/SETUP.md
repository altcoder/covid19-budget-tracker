# Local Development

1. Clone this repo.

```
$ git clone https://github.com/altcoder/covid19-budget-tracker.git
$ cd covid19-budget-tracker
```

2. Install Docker (skip if already installed)

3. Setup Airflow variables

**config/airflow-vars.json** contains airflow credential variables that you would need to
access external data sources. This is optional for local setup. 
```
$ cp config/airflow-vars-sample.json config/airflow-vars.json
[edit airflow-vars.json]
```

4. Setup Fernet keys and authentication
```
$ scripts/airflow.sh init
```

5. Generate Google OAuth Token (optional)

If you are planning to use Google API to access public google sheets or
google drive. You need a Google OAuth 2.0 Client ID json file and run the
script below.  
```
$ scripts/g_oauth_token.sh [path_to_json_file]
```

This will generate `g_oauth_clt.pickle` to use for authenticating access to
Google APIs.


6. Start Airflow container (SequentialExecutor)
```
$ scripts/airflow.sh start
```

7. View Airflow container logs (optional)
```
$ scripts/airflow.sh logs
```

8. List Airflow DAGs (testing) 
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

8. (Optional) If you change requirements.txt make sure to rebuild the image. Otherwise, if you only changed DAG python codes just restart.
```
$ scripts/airflow.sh build
$ scripts/airflow.sh restart
```

9. (Optional) If you rebuild make sure to re-apply the authentication settings.

# Integration Test

1. Start Airflow container (SequentialExecutor)
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

2. For SequentialExecutor:
```
$ scripts/airflow.sh start
$ scripts/airflow.sh logs
```

3. For LocalExecutor:
```
$ scripts/airflow.sh exec_local_up
...
$ scripts/airflow.sh exec_local_down
```

4. For CeleryExecutor:
```
$ scripts/airflow.sh exec_celery_up
...
$ scripts/airflow.sh exec_celery_down
```

5. For Astronomer:

```
$ astro dev init
$ astro dev start
$ astro deploy
```
6. Setup authentication

Run init to setup fernet keys
```
$ scripts/airflow.sh init
```

This will perform the following changes:
- Replace the fernet key in `config/airflow-prod.cfg`  
```
[core]
fernet_key = [FERNET_KEY]
```
- And in `scripts/docker-entrypoint.sh`  
```
: "${AIRFLOW__CORE__FERNET_KEY:="[FERNET_KEY]"}"
```

Next, modify `config/airflow-prod.cfg` and enable authentication  
```
[webserver]
...
authenticate = True
auth_backend = airflow.contrib.auth.backends.password_auth
```
Next, Generate user following [this
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
7. Permissions (Known Issue)

If DAGs are not running because of permission issues in your docker image. Just
make sure airflow:airflow users has access to the following files and
directories.

```
credentials/[your_google_oauth_token.pickle] (read/write)
output/ (read/write/execute)
datasets/ (read/write/execute)
datasets/* (read/write)
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

# Continuous Integration

This project uses Github Workflows for CI.

You will need to encypt and publish the token used for Google API in order for
tests to pass:

```
$ scripts/g_oauth_token.sh [path to google api json token]
$ scripts/encrypt_tokens.sh
```

Commit your changes.

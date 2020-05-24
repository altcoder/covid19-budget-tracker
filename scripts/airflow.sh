#!/usr/bin/env bash

run_airflow() {
  docker rm ${PWD##*/}
  docker run -d \
      --name=${PWD##*/} \
      -p 8080:8080 \
      -v $PWD/dags:/usr/local/airflow/dags \
      -v $PWD/notebooks:/usr/local/airflow/notebooks \
      -v $PWD/datasets:/usr/local/airflow/datasets \
      -v $PWD/output:/usr/local/airflow/output \
      -v $PWD/config:/usr/local/airflow/config \
      altcoder/docker-airflow webserver
}

stop_airflow() {
  docker stop ${PWD##*/}
}

case "$1" in
  vars)
    docker exec -it ${PWD##*/} airflow variables -i /usr/local/airflow/config/airflow-vars.json
    ;;
  build)
    docker build --no-cache --rm -t altcoder/docker-airflow .
    ;;
  exec_local_up)
    docker-compose -f docker-compose-LocalExecutor.yml up -d
    ;;
  exec_local_down)
    docker-compose -f docker-compose-LocalExecutor.yml down
    ;;
  exec_celery_up)
    docker-compose -f docker-compose-CeleryExecutor.yml up -d
    ;;
  exec_celery_down)
    docker-compose -f docker-compose-CeleryExecutor.yml down
    ;;
  publish)
    docker push altcoder/docker-airflow:latest
    ;;
  start)
    run_airflow
    ;;
  stop)
    stop_airflow
    ;;
  restart)
    stop_airflow
    run_airflow
    ;;
  logs)
    docker logs -f ${PWD##*/}
    ;;
  list_dags)
    docker exec -it ${PWD##*/} airflow list_dags
    ;;
  trigger_dag|test|unpause)
    cmd=$1
    shift
    docker exec -it ${PWD##*/} airflow "$cmd" "$@"
    ;;
  run)
    shift
    docker exec -it ${PWD##*/} airflow "$@"
    ;;
  sh)
    docker exec -it  ${PWD##*/} /bin/bash
    ;;
  *)
    echo "Options: vars, build, exec_local_up, exec_local_down, exec_celery_up, exec_celery_down, publish, start, stop, restart, logs, list_dags, trigger_dag, test, unpause, run"
    ;;
esac

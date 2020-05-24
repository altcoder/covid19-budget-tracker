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
  docker exec -it ${PWD##*/} airflow variables -i /usr/local/config/airflow-vars.json

}

stop_airflow() {
  docker stop ${PWD##*/}
}

case "$1" in
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
    shift
    docker exec -it ${PWD##*/} airflow trigger_dag "$1" "$@"
    ;;
  run)
    shift
    docker exec -it ${PWD##*/} airflow "$@"
    ;;
  *)
    echo "Options: start, stop, restart, logs, list_dags, trigger_dag, test, unpause, run"
    ;;
esac

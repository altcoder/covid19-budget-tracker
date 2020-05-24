# Open Source Data Project Template

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://raw.githubusercontent.com/altcoder/covid19-budget-tracker/master/LICENSE)
![Airflow/DAG](https://github.com/altcoder/covid19-budget-tracker/workflows/Airflow/DAG/badge.svg)

My Project template for Open Source Data Projects

## Quickstart

1. Clone this repo.

```
$ git clone https://github.com/altcoder/covid19-budget-tracker.git
$ cd covid19-budget-tracker
```

2. You will need Docker to run the airflow container 

``` 
$ scripts/airflow.sh start
```

3. Run trigger Airflow DAG

```
$ scripts/airflow.sh trigger_dag github_poll_trigger -e 2020-05-16
```

4. View generated files in output directory 

```
$ ls output
```

## Developers

This project uses Apache Airflow to run Python Notebooks as jobs. Follow [this instuctions](docs/SETUP.md) to setup your local development environment. 

## Contributing

Contributions are always welcome, no matter how large or small. Before contributing,
please read the [guide](.github/CONTRIBUTION.md) and [code of conduct](.github/CODE_OF_CONDUCT.md).

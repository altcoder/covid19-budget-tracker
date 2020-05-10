# Philippines COVID19 Budget Tracker

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://raw.githubusercontent.com/altcoder/covid19-budget-tracker/master/LICENSE)
![Airflow/DAG](https://github.com/altcoder/covid19-budget-tracker/workflows/Airflow/DAG/badge.svg)

Philippine government's COVID19 budget datasets for citizen's tracking

## Quickstart

1. Clone this repo.

```
$ git clone https://github.com/[GITHUB_USERNAME]/[REPO_NAME].git
$ cd [REPO_NAME]
```

2. Setup your Python dependencies

``` 
$ pip install -r requirements-airflow.txt
$ pip install -r requirements.txt
```

3. Set environment variables

```
$ ./init.sh
$ airflow upgradedb
```

4. Run airflow tasks
```
$ airflow etl_covid19_budget_tracker execute_notebook 2020-05-01
```

5. View generated csv files in output directory 

```
$ ls output
```

## Development

This project uses Apache Airflow to run Python Notebooks as jobs. Follow [this instuctions](docs/SETUP.md) to setup your local development environment. 

#### Official Source 

[COVID19 Philippines Citizens' Budget Tracker](https://docs.google.com/spreadsheets/d/1sjovcOhYY2KY3Tq3zV56rb1kPrK52SuEyJ7PWG8vOuY/edit?usp=sharing)


## CONTRIBUTING

Contributions are always welcome, no matter how large or small. Before contributing,
please read the [code of conduct](.github/CODE_OF_CONDUCT.md).

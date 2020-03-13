import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from dags.airflow_utils import (
    DBT_IMAGE,
    dbt_install_deps_and_seed_cmd,
    dbt_install_deps_cmd,
    clone_and_setup_extraction_cmd,
    mm_failed_task,
    pod_defaults,
    pod_env_vars,
    xs_warehouse,
)
from dags.kube_secrets import (
    SNOWFLAKE_ACCOUNT,
    SNOWFLAKE_PASSWORD,
    SNOWFLAKE_TRANSFORM_ROLE,
    SNOWFLAKE_TRANSFORM_SCHEMA,
    SNOWFLAKE_TRANSFORM_WAREHOUSE,
    SNOWFLAKE_USER,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    PG_IMPORT_BUCKET,
    HEROKU_POSTGRESQL_URL,
    SSH_KEY,
)

# Load the env vars into a dict and set Secrets
env = os.environ.copy()
env_vars = {**pod_env_vars, **{}}

# Default arguments for the DAG
default_args = {
    "catchup": False,
    "depends_on_past": False,
    "owner": "airflow",
    "on_failure_callback": mm_failed_task,
    "retries": 0,
    "retry_delay": timedelta(minutes=1),
    "sla": timedelta(hours=8),
    "start_date": datetime(2019, 1, 1, 0, 0, 0),
}

# Create the DAG
dag = DAG("dbt_nightly", default_args=default_args, schedule_interval="0 8 * * *")

# dbt-run
dbt_run_cmd = f"""
    {dbt_install_deps_cmd} &&
    SNOWFLAKE_TRANSFORM_WAREHOUSE=transform_l dbt run --profiles-dir profile --models tag:nightly
"""

dbt_seed = KubernetesPodOperator(
    **pod_defaults,
    image=DBT_IMAGE,
    task_id="dbt-seed",
    name="dbt-seed",
    secrets=[
        SNOWFLAKE_ACCOUNT,
        SNOWFLAKE_USER,
        SNOWFLAKE_PASSWORD,
        SNOWFLAKE_TRANSFORM_ROLE,
        SNOWFLAKE_TRANSFORM_WAREHOUSE,
        SNOWFLAKE_TRANSFORM_SCHEMA,
        SSH_KEY,
    ],
    env_vars=env_vars,
    arguments=[dbt_install_deps_and_seed_cmd],
    dag=dag,
)


dbt_run = KubernetesPodOperator(
    **pod_defaults,
    image=DBT_IMAGE,
    task_id="dbt-run",
    name="dbt-run",
    secrets=[
        SNOWFLAKE_ACCOUNT,
        SNOWFLAKE_USER,
        SNOWFLAKE_PASSWORD,
        SNOWFLAKE_TRANSFORM_ROLE,
        SNOWFLAKE_TRANSFORM_WAREHOUSE,
        SNOWFLAKE_TRANSFORM_SCHEMA,
        SSH_KEY,
    ],
    env_vars=env_vars,
    arguments=[dbt_run_cmd],
    dag=dag,
)

dbt_seed >> dbt_run
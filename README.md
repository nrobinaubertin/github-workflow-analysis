Github workflow analysis
========================

The goal of this repository is to propose a quick and direty way to extract data from your pipeline for analysis.

## Getting started

1. Create a [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)
2. Create a `config.json` file. Here is an example:
```
{
  "token": "ghp_personalaccesstoken",
  "owner": "username_or_organization",
  "repositories": [
    "repository_name"
  ],
  "db_dsn": "postgresql://postgres:mysecretpassword@172.17.0.3/postgres",
}
```
3. Deploy [postgres using docker](https://hub.docker.com/_/postgres)
4. Install dependencies: `pip install --user -r requirements.txt`
5. Launch the script to extract the data from your pipelines: `python3 ./main.py`
6. Deploy [metabase using docker](https://hub.docker.com/r/metabase/metabase)
7. Connect your database to metabase and start analysing !

## Some possible analysis

### Number of runs per day
```
SELECT
    conclusion,
    COUNT(runs.id) as count,
    date(runs.run_started_at) as day
FROM
    runs
LEFT JOIN repositories ON runs.repository_id = repositories.id
WHERE
    repositories.name = {{repository}}
GROUP BY conclusion, "day"
ORDER BY day ASC
LIMIT
  1048575;
```

![number of runs per day](screenshots/runs.jpeg)

### Duration of long operations
```
SELECT
    "public"."steps"."name" AS "name",
    AVG(extract(epoch from steps.completed_at::timestamp - steps.started_at::timestamp)) AS avg_duration,
    date(runs.run_started_at) AS day
FROM
    "public"."steps"
LEFT JOIN jobs ON steps.job_id = jobs.id
LEFT JOIN runs ON jobs.run_id = runs.id
LEFT JOIN repositories ON runs.repository_id = repositories.id
WHERE
    repositories.name = {{repository}}
    AND "public"."steps"."status" = 'completed'
    AND "public"."steps"."conclusion" = 'success'
GROUP BY steps.name, "day"
HAVING
    AVG(extract(epoch from steps.completed_at::timestamp - steps.started_at::timestamp)) > 180
ORDER BY day ASC
LIMIT
    1048575
```

![Duration of long operations](screenshots/long-ops.jpeg)

### Average retries before successful run
```
SELECT
  "public"."runs"."name" AS "name",
  AVG("public"."runs"."run_attempt") AS "avg_run_attempt",
  date(runs.created_at) as day
FROM
  "public"."runs"
LEFT JOIN repositories ON runs.repository_id = repositories.id
WHERE
    repositories.name = {{repository}}
    AND runs.conclusion = 'success'
GROUP BY runs.name, "day"
HAVING
    AVG("public"."runs"."run_attempt") > 1
LIMIT
  1048575
```

![Average retries](screenshots/retries.jpeg)

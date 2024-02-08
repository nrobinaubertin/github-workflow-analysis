Average retries before successful run
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

Duration of long operations
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

k8s integ test failure type per day
```
SELECT
date(runs.run_started_at) as day,
CASE
  WHEN logs.log_content LIKE '%unknown container reason "ImagePullBackOff"%' THEN 'ImagePullBackOff'
  WHEN logs.log_content LIKE '%Timed out waiting for model%' THEN 'Timed out waiting for model'
  WHEN logs.log_content LIKE '%agent lost, see ''juju show-status-log nginx-ingress-integrator%' THEN 'Agent lost: nginx-ingress-integrator'
  WHEN logs.log_content LIKE '%agent lost, see ''juju show-status-log postgresql-k8s%' THEN 'Agent lost: postgres'
  WHEN logs.log_content LIKE '%agent lost, see ''juju show-status-log redis%' THEN 'Agent lost: redis'
  WHEN logs.log_content LIKE '%agent lost, see ''juju show-status-log prometheus-k8s%' THEN 'Agent lost: prometheus'
  WHEN logs.log_content LIKE '%agent lost, see ''juju show-status-log synapse%' THEN 'Agent lost: synapse'
  WHEN logs.log_content LIKE '%agent lost, see ''juju show-status-log indico%' THEN 'Agent lost: indico'
  WHEN logs.log_content LIKE '%Unit in error: postgresql-k8s%' THEN 'Unit in error: postgres'
  WHEN logs.log_content LIKE '%Unit in error: redis%' THEN 'Unit in error: redis'
  WHEN logs.log_content LIKE '%Unit in error: prometheus-k8s%' THEN 'Unit in error: prometheus'
  WHEN logs.log_content LIKE '%Unit in error: synapse%' THEN 'Unit in error: synapse'
  WHEN logs.log_content LIKE '%Unit in error: indico%' THEN 'Unit in error: indico'
  WHEN logs.log_content LIKE '%Unit in error: nginx-ingress-integrator%' THEN 'Unit in error: nginx-ingress-integrator'
  WHEN logs.log_content LIKE '%test_health_checks%FAILED%' THEN 'test_health_checks FAILED'
  WHEN logs.log_content LIKE '%grafana%hook failed: "install"%' THEN 'Grafana install failed'
  WHEN logs.log_content LIKE '%Charm feature requirements cannot be met%' THEN 'Requires newer juju'
  ELSE 'Other'  -- Handle cases that don't match any of the specific failures
END as failure_type,
COUNT(*) as count
FROM
  runs
  JOIN logs ON runs.id = logs.run_id
  JOIN repositories ON runs.repository_id = repositories.id
WHERE
  logs.log_identifier LIKE '%Run k8s%'
  AND runs.conclusion = 'failure'
  AND repositories.name = {{repository}}
GROUP BY
  day,
  failure_type
ORDER BY
  day;
```

Number of runs per day
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

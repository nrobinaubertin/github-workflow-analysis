import sqlite3


def create_connection(sqlite_file):
    conn = None
    try:
        conn = sqlite3.connect(sqlite_file)
        return conn
    except sqlite3.Error as e:
        print(e)

    return conn


def create_tables(conn):
    runs_table = """CREATE TABLE IF NOT EXISTS runs (
        id integer PRIMARY KEY,
        name text NOT NULL,
        head_branch text,
        head_sha text,
        path text,
        display_title text,
        run_number integer,
        event text,
        status text,
        conclusion text,
        workflow_id integer,
        check_suite_id integer,
        url text,
        created_at text,
        updated_at text,
        run_attempt integer,
        run_started_at text,
        workflow_url text,
        actor_id integer,
        commit_id text,
        referenced_workflow_sha text,
        repository_id integer
    ); """

    actors_table = """CREATE TABLE IF NOT EXISTS actors (
        id integer PRIMARY KEY,
        login text NOT NULL,
        url text,
        type text,
        site_admin bool
    ); """

    commits_table = """CREATE TABLE IF NOT EXISTS commits (
        id text PRIMARY KEY,
        tree_id text,
        message text,
        timestamp text,
        author_name text,
        author_email text,
        committer_name text,
        committer_email text
    ); """

    repositories_table = """CREATE TABLE IF NOT EXISTS repositories (
        id integer PRIMARY KEY,
        name text NOT NULL,
        full_name text,
        private bool,
        owner_login text,
        owner_id integer,
        url text,
        site_admin bool,
        html_url text,
        description text,
        fork bool
    ); """

    jobs_table = """CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY,
        run_id INTEGER NOT NULL,
        workflow_name TEXT NOT NULL,
        head_branch TEXT NOT NULL,
        run_url TEXT NOT NULL,
        run_attempt INTEGER NOT NULL,
        head_sha TEXT NOT NULL,
        url TEXT NOT NULL,
        html_url TEXT NOT NULL,
        status TEXT NOT NULL,
        conclusion TEXT,
        created_at TEXT NOT NULL,
        started_at TEXT NOT NULL,
        completed_at TEXT,
        name TEXT NOT NULL,
        check_run_url TEXT NOT NULL,
        labels TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES runs (id)
    )"""

    steps_table = """CREATE TABLE IF NOT EXISTS steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        status TEXT NOT NULL,
        conclusion TEXT,
        number INTEGER NOT NULL,
        started_at TEXT,
        completed_at TEXT,
        FOREIGN KEY (job_id) REFERENCES jobs (id)
    )"""

    logs_table = """
    CREATE TABLE logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER, 
        log_identifier TEXT,
        log_content TEXT,
        FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
    );
    """

    try:
        c = conn.cursor()
        c.execute(runs_table)
        c.execute(actors_table)
        c.execute(commits_table)
        c.execute(repositories_table)
        c.execute(jobs_table)
        c.execute(steps_table)
        c.execute(logs_table)
    except sqlite3.Error as e:
        print(e)


def setup_database(sqlite_file):
    conn = create_connection(sqlite_file)

    if conn is not None:
        create_tables(conn)
    else:
        print("Error! Cannot create the database connection.")


def insert_actor(conn, actor):
    sql = """ INSERT INTO actors(id,login,url,type,site_admin)
              VALUES(?,?,?,?,?)
              ON CONFLICT(id) DO NOTHING """
    cur = conn.cursor()
    cur.execute(sql, actor)
    return cur.lastrowid


def insert_commit(conn, commit):
    sql = """ INSERT INTO commits(id,tree_id,message,timestamp,author_name,author_email,
                                  committer_name,committer_email)
              VALUES(?,?,?,?,?,?,?,?)
              ON CONFLICT(id) DO NOTHING """
    cur = conn.cursor()
    cur.execute(sql, commit)
    return cur.lastrowid


def insert_repository(conn, repository):
    sql = """ INSERT INTO repositories(id,name,full_name,private,owner_login,owner_id,url,site_admin,html_url,description,fork)
              VALUES(?,?,?,?,?,?,?,?,?,?,?)
              ON CONFLICT(id) DO NOTHING """
    cur = conn.cursor()
    cur.execute(sql, repository)
    return cur.lastrowid


def insert_run(conn, run):
    sql = """ INSERT INTO runs(
                id,
                name,
                head_branch,
                head_sha,
                path,
                display_title,
                run_number,
                event,
                status,
                conclusion,
                workflow_id,
                check_suite_id,
                url,
                created_at,
                updated_at,
                run_attempt,
                run_started_at,
                workflow_url,
                actor_id,
                commit_id,
                referenced_workflow_sha,
                repository_id
           )
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
              ON CONFLICT(id) DO NOTHING """
    cur = conn.cursor()
    cur.execute(sql, run)
    return cur.lastrowid


def insert_job(conn, job):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO jobs (
            id, run_id, workflow_name, head_branch, run_url,
            run_attempt, head_sha, url, html_url, status,
            conclusion, created_at, started_at, completed_at, 
            name, check_run_url, labels
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO NOTHING
    """,
        (
            job["id"],
            job["run_id"],
            job["workflow_name"],
            job["head_branch"],
            job["run_url"],
            job["run_attempt"],
            job["head_sha"],
            job["url"],
            job["html_url"],
            job["status"],
            job["conclusion"],
            job["created_at"],
            job["started_at"],
            job["completed_at"],
            job["name"],
            job["check_run_url"],
            ",".join(job["labels"]),
        ),
    )

    conn.commit()


def insert_step(conn, step, job_id):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO steps (
            job_id, name, status, conclusion, number, started_at, completed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            job_id,
            step["name"],
            step["status"],
            step["conclusion"],
            step["number"],
            step["started_at"],
            step["completed_at"],
        ),
    )

    conn.commit()


def run_exists(conn, run_id):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 1 FROM runs WHERE id=?
    """,
        (run_id,),
    )

    result = cursor.fetchone()

    return result is not None

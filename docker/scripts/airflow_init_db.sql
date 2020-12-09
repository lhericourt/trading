SELECT 'CREATE DATABASE airflow OWNER admin'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec
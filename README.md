# Trading Project
## Init project
  - Use the docker-compose file to run postgres and airflow
  - Use the script database > apply_migration to initialize the database (schema and tables)
  - If you need data, restore a database backup
# Database
## Backup & restore
Do the backup and restore from inside the container, from my Mac it does not work
Command to backup the schema trading : 
- `cd /var/lib/postgresql/data`
- `mkdir backup`
- `pg_dump -U admin -x -Fc -n trading --no-owner trading > backup/trading_history_$(date +%Y%m%d)`

Command to restore the schema from inside the container:
- `cd /var/lib/postgresql/data/backup`
- `pg_restore -c -d trading -n trading trading_history_XXXXXXXX -U admin`

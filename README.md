# oracleDUMP

python script designed to connect to an oracle db, extract ddl (data definition language) scripts for specified db objects, and save them to a local directory. it handles wrapped ddl scripts by unwrapping them before saving. 

# use case
handy for DBAs and devs who need to back up or inspect database object definitions.

# features
- configurable db connection: connects to oracle dbs using credentials specified in an extern `config.ini` file. 
- cli: specify dump path, object types, and users thru command line args for flexibility.
- wrapped DDL handling: detects and unwraps encoded DDL scripts, ensuring correct format for analysis or backup. 
- error handling: manages exceptions and provides useful debug information (new)
- logging: logging for output (new)
- security: parametrized SQL queries to mitigate SQLi risks (new)

# requirements
- python 3.x
- oracle instant client
- cx_Oracle module http://cx-oracle.sourceforge.net/

# setup
1. make sure oracle instant client is installed and `ORACLE_HOME` is set
2. install cx_Oracle module: `pip install cx_Oracle`
3. create a `config.ini` file with the db connection string

# usage
```css
python oracleDUMP.py --dump-path "path/to/dump" --object_types PACKAGE PROCEDURE --users user1 user2
```

# config
the `config.ini` file should contain the following section:
```csharp
[database]
connection_string = YOUR_CONNECTION_STRING
```

# some examples

1. logging
```yaml
2023-11-24 10:00:00 - INFO - connected to the db!
2023-11-24 10:00:02 - INFO - dumping objects for owner: user1
2023-11-24 10:00:03 - INFO - saving file: DDL/user1/MyPackage_PACKAGE.sql
2023-11-24 10:00:05 - INFO - dumping objects for owner: user2
2023-11-24 10:00:06 - INFO - saving file: DDL/user2/MyProcedure_PROCEDURE.sql
```

2. errors
```vbnet
2023-11-24 10:00:10 - ERROR - error in main function: [cx_Oracle.DatabaseError] ORA-12154: TNS:could not resolve the connect identifier specified
```

or 

```vbnet
2023-11-24 10:00:15 - ERROR - error saving file DDL/user1/MyPackage_PACKAGE.sql: [Errno 13] Permission denied: 'DDL/user1/MyPackage_PACKAGE.sql'
```

3. command line arg usage
```css
python oracleDUMP.py --dump_path "/home/user/oracle_ddl" --object_types PACKAGE BODY --users admin
```

4. success
```yaml
2023-11-24 10:05:00 - INFO - Done.
```
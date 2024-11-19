import sqlite3
import os

# define database files
database_name = "lieferpatz_database.sqlite"
sql_file = "database.sql"


# check if the database file exists and delete it first
if os.path.exists(database_name):
    os.remove(database_name)


try:
    # try connecting to the new dabase to be crerated
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    # read our sql file
    with open(sql_file, 'r') as sql_file_content:
        sql_script = sql_file_content.read()

    # execute the commands in the sql file
    cursor.executescript(sql_script)
    # save the changes to our jnew database
    connection.commit()

    # close our connection to the database
    connection.close()

    # tell user db was created successfuly
    print(f"Database {database_name} has been created successfully")

except sqlite3.Error as e:
    # if we faced any error then print it here
    print(e)

import streamlit as st
import sqlite3
import pandas as pd
import os
import requests
import shutil

# URL for the SQLite backup and the local file name
DB_URL = "https://storage.googleapis.com/benchmarks-artifacts/travel-db/travel2.sqlite"
SAVE_DIR = "./src/sqlite_db"
DB_NAME = "travel2.sqlite"
BACKUP_FILE = "travel2.backup.sqlite"
DOC_PATH = os.path.join(SAVE_DIR, DB_NAME)
BACKUP_PATH = os.path.join(SAVE_DIR, BACKUP_FILE)


def download_db():
    """Download the SQLite database file if it does not already exist."""
    # The backup lets us restart for each tutorial section
    if not os.path.exists(DOC_PATH):
        # st.info("Downloading the SQLite database...")
        os.makedirs(SAVE_DIR, exist_ok=True)
        response = requests.get(DB_URL)
        response.raise_for_status()  # Ensure the request was successful
        with open(DOC_PATH, "wb") as f:
            f.write(response.content)
        # Backup - we will use this to "reset" our DB in each section
        shutil.copy(DOC_PATH, BACKUP_PATH)

    #     st.success("Database downloaded successfully!")
    # else:
    #     st.info("Database file already exists locally.")
        print("Sqlite database downloaded successfully!")
    else:
        # Replace travel2.sqlite from the backup file
        print("Resetting sqlite backup")
        os.remove(DOC_PATH)
        shutil.copy(BACKUP_PATH, DOC_PATH)

    # Convert the flights to present time for our tutorial
    update_dates(DOC_PATH)


# Convert the flights to present time for our tutorial
def update_dates(file):
    shutil.copy(BACKUP_PATH, file)
    conn = sqlite3.connect(file)
    cursor = conn.cursor()

    tables = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table';", conn
    ).name.tolist()
    tdf = {}
    for t in tables:
        tdf[t] = pd.read_sql(f"SELECT * from {t}", conn)

    example_time = pd.to_datetime(
        tdf["flights"]["actual_departure"].replace("\\N", pd.NaT)
    ).max()
    current_time = pd.to_datetime("now").tz_localize(example_time.tz)
    time_diff = current_time - example_time + pd.Timedelta(days=31)

    tdf["bookings"]["book_date"] = (
        pd.to_datetime(tdf["bookings"]["book_date"].replace("\\N", pd.NaT), utc=True)
        + time_diff
    )

    datetime_columns = [
        "scheduled_departure",
        "scheduled_arrival",
        "actual_departure",
        "actual_arrival",
    ]
    for column in datetime_columns:
        tdf["flights"][column] = (
            pd.to_datetime(tdf["flights"][column].replace("\\N", pd.NaT)) + time_diff
        )

    for table_name, df in tdf.items():
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    del df
    del tdf
    conn.commit()
    conn.close()

    return file


def run_query(query):
    """Run a SQL query on the SQLite database and return the results as a DataFrame."""
    try:
        with sqlite3.connect(DOC_PATH) as conn:
            df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None





# Streamlit user interface
# st.title("SQLite Query Web Interface")
# st.markdown("""
# Enter your SQL query below and execute it to see the results displayed as a DataFrame.
# """)
#
# download_db()
#
# # Default query: lists a few entries from the SQLite metadata table
# default_query = "SELECT * FROM sqlite_master LIMIT 10;"
# query = st.text_area("SQL Query", default_query, height=150)
#
# if st.button("Run Query"):
#     result_df = run_query(query)
#     if result_df is not None:
#         st.write("Query Results:")
#         st.dataframe(result_df)
#

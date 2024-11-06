import configparser
import uuid

def read_config_file(file_path):
    config = configparser.ConfigParser()
    try:
        config.read(file_path)
        return config
    except Exception as e:
        return f"An error occurred: {e}"

# Example usage
config = read_config_file('Trade.conf')
if isinstance(config, configparser.ConfigParser):
    for section in config.sections():
        print(f"Section: {section}")
        for key, value in config.items(section):
            print(f"{key} = {value}")
else:
    print(config)

def rows_to_dict(rows):
    return [dict(zip([column[0] for column in rows.description], row)) for row in rows]





def create_table(cursor, table_name, supported_assets):
    # Create the balances table if it doesn't exist
    query = f'''CREATE TABLE IF NOT EXISTS {table_name} (
        address TEXT PRIMARY KEY
    '''
    for asset in supported_assets:
        query += f', {asset} REAL'
    query += ');'
    cursor.execute(query)

    # Check existing columns in the balances table
    existing_columns_query = f"PRAGMA table_info({table_name});"
    cursor.execute(existing_columns_query)
    existing_columns = [row[1] for row in cursor.fetchall()]

    # Add new columns for any assets not already in the table
    for asset in supported_assets:
        if asset not in existing_columns:
            alter_table_query = f"ALTER TABLE {table_name} ADD COLUMN {asset} REAL;"
            cursor.execute(alter_table_query)

    # Remove columns for assets no longer supported
    columns_to_remove = [col for col in existing_columns if col != 'address' and col not in supported_assets]
    if columns_to_remove:
        # Create a new table with the desired columns
        new_table_name = f"{table_name}_new"
        new_query = f'''CREATE TABLE {new_table_name} (
            address TEXT PRIMARY KEY
        '''
        for asset in supported_assets:
            new_query += f', {asset} REAL'
        new_query += ');'
        cursor.execute(new_query)

        # Copy data from the old table to the new table
        columns_to_keep = ', '.join(['address'] + [asset for asset in supported_assets if asset in existing_columns])
        copy_data_query = f"INSERT INTO {new_table_name} ({columns_to_keep}) SELECT {columns_to_keep} FROM {table_name};"
        cursor.execute(copy_data_query)

        # Drop the old table and rename the new table
        cursor.execute(f"DROP TABLE {table_name};")
        cursor.execute(f"ALTER TABLE {new_table_name} RENAME TO {table_name};")

    return existing_columns


def generate_unique_id():
    return str(uuid.uuid4())


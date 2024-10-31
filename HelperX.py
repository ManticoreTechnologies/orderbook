import configparser

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
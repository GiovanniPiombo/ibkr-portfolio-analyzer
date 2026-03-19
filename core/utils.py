import json

def read_json(file, parameter_name=None):
    """
    Read a JSON file and return the value of a specific parameter or the whole dictionary if no parameter is specified.
    """
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # if parameter_name is provided, return that specific value, otherwise return the whole dictionary
        if parameter_name:
            return data.get(parameter_name)
        return data

    except FileNotFoundError:
        print(f"Error: {file} file not found.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: {file} is not a valid JSON.")
        exit(1)

def format_json(data):
    """Utility function to format a dictionary as a JSON string."""
    return json.dumps(data, indent=4, ensure_ascii=False)

def write_json(file, data):
    """
    Write a dictionary to a JSON file in a formatted way.
    """
    try:
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error writing {file}: {e}")
        return False
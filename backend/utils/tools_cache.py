_search_tools = None
_python_tools = None
_time_tools = None


def set_tools(search, python, time):
    global _search_tools, _python_tools, _time_tools
    _search_tools = search
    _python_tools = python
    _time_tools = time


def get_search_tools():
    return _search_tools


def get_python_tools():
    return _python_tools


def get_time_tools():
    return _time_tools

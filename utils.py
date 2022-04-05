def split_check(s: str, l: list) -> list:
    if s is None:
        return []
    str_list = s.split(',')
    for sub_str in str_list:
        if sub_str not in l:
            raise ValueError("No such element in list")
    return str_list

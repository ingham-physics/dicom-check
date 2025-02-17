from typing import List, Tuple


def is_series_present(series: List[dict]) -> Tuple[bool, str]:
    """
    Check if the series list is not empty.

    Args:
        series (List[dict]): A list of dictionaries representing series.

    Returns:
        Tuple[bool, str]: A tuple where the first element is a boolean indicating
                          if the series list is not empty, and the second element
                          is a string message. If the series list is empty, the
                          message will be "No series found".
    """
    if len(series) > 0:
        return True, ""

    return False, "No series found"


def check_series_count(series: List[dict], n: int, op: str) -> Tuple[bool, str]:
    """
    Check the count of series against a specified number using a given operator.

    Args:
        series (List[dict]): A list of series dictionaries.
        n (int): The number to compare the series count against.
        op (str): The comparison operator. Can be one of 'eq', 'gt', 'lt', 'gte', 'lte'.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if the condition is met,
                          and an error message if the condition is not met.

    Raises:
        ValueError: If an invalid operator is provided.
    """
    result = False
    if op == "eq":
        result = len(series) == n
    elif op == "gt":
        result = len(series) > n
    elif op == "lt":
        result = len(series) < n
    elif op == "gte":
        result = len(series) >= n
    elif op == "lte":
        result = len(series) <= n
    else:
        raise ValueError("Invalid operator")

    if not result:
        return result, f"Expected {op} {n} but found {len(series)}"

    return result, ""


def check_structures_present(
    series: List[dict], structures: dict, case_sensitive: bool = True
) -> Tuple[bool, str]:
    """
    Check if specified structures are present in the given series.

    Args:
        series (List[dict]): A list of dictionaries, each representing a series with a key
            "structure_names" containing a list of structure names and a key "series_uid"
            for the series identifier.
        structures (dict): A dictionary where keys are structure names to check for, and
            values are lists of allowed variants for each structure.
        case_sensitive (bool, optional): Whether the check should be case-sensitive.
            Defaults to True.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if all structures are
            present, and a string with details of any missing structures.
    """
    result = True
    output = ""

    for s in series:
        structures_present = s["structure_names"]

        for structure in structures:
            allowed_variants = list(set([structure] + structures[structure]))
            found = False
            for variant in allowed_variants:
                if case_sensitive:
                    if variant in structures_present:
                        found = True
                        break
                else:
                    if variant.lower() in [s.lower() for s in structures_present]:
                        found = True
                        break

            if not found:
                result = False
                output += f"{structure} not found in series {s['series_uid']}\n"

    return result, output


def check_meta_value(series: List[dict], key: str, value: str) -> Tuple[bool, str]:
    """
    Checks if a specified key in each dictionary of a list has a specific value.

    Args:
        series (List[dict]): A list of dictionaries representing series metadata.
        key (str): The key to check in each dictionary.
        value (str): The value to compare against the value associated with the key.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if all checks passed,
            and a string with details of any mismatches or missing keys.
    """
    result = True
    output = ""

    for s in series:
        if key not in s:
            result = False
            output += f"Key {key} not found in series {s['series_uid']}\n"
        elif s[key] != value:
            result = False
            output += f"Value of {key} not {value} in series {s['series_uid']}\n"

    return result, output


def check_all_in_same(series: List[dict], key: str) -> Tuple[bool, str]:
    """
    Checks if all series have the same value for a given key.

    Args:
        series (List[dict]): A list of dictionaries to check.
        key (str): The key to check in each dictionary.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if all values are the same,
            and a string message indicating the number of unique values found if they are
            not the same.
    """
    result = True
    output = ""

    frame_of_references = []

    for s in series:
        frame_of_references.append(s[key])

    unique_for = list(set(frame_of_references))

    if len(unique_for) > 1:
        result = False
        output = f"{len(unique_for)} {key}s found"

    return result, output


def check_linked(series: List[dict], from_name: str, to_name: str) -> Tuple[bool, str]:
    """Checks if all series with a specific 'from_name' are linked to a series with 'to_name'.
    Args:
        series (List[dict]): A list of dictionaries where each dictionary represents a series.
            Each dictionary must contain 'match' and 'series_uid' keys.
            Optionally, it may contain a 'referenced_series' key which is a list of series UIDs.
        from_name (str): The name to check for in the 'match' key of the series.
        to_name (str): The name to check for in the 'match' key of the linked series.
    Returns:
        Tuple[bool, str]: A tuple containing:
            - A boolean indicating if all series with 'from_name' are linked to a series with
              'to_name'.
            - A string with details of any series that are not linked.
    """
    result = True
    output = ""

    for s in series:
        if s["match"] == from_name:
            linked = False
            for s2 in series:
                if s2["match"] == to_name and s["series_uid"] == s2.get(
                    "referenced_series", []
                ):
                    linked = True
                    break

            if not linked:
                # Try to link via frame_of_reference
                for s2 in series:
                    if (
                        s2["match"] == to_name
                        and s["frame_of_reference"] == s2["frame_of_reference"]
                    ):
                        linked = True
                        break

                if not linked:
                    result = False
                    output += f"Series {s['series_uid']} not linked to {to_name}\n"

    return result, output

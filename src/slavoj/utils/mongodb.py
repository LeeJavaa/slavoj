from typing import Dict, Any, TypeVar, List, Union

T = TypeVar('T')


def strip_mongo_id(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[
    Dict[str, Any], List[Dict[str, Any]]]:
    """Remove MongoDB _id field from document or list of documents"""
    if isinstance(data, list):
        return [strip_mongo_id(item) for item in data]

    if isinstance(data, dict):
        return {k: v for k, v in data.items() if k != '_id'}

    return data
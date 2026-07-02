"""Utilities for managing Open WebUI knowledge collections."""

from collections import defaultdict
from json import dumps

from requests import get, post

from utils.config.logger import get_logger

logger = get_logger(__name__)


def transform_list_of_knowledge_to_dict(knowledge_list) -> dict:
    """Transform a list or paginated response of knowledge items into a nested dictionary.

    Args:
        knowledge_list: Either a list of knowledge items or a paginated response dict
            containing an 'items' list.

    Returns:
        Nested dict keyed by user_id → knowledge_name → {'knowledge_id', 'files_ids'}.
    """
    if isinstance(knowledge_list, dict) and 'items' in knowledge_list:
        items = knowledge_list.get('items', [])
    else:
        items = knowledge_list or []

    knowledge_new_dict = defaultdict(defaultdict)

    for element in items:
        user_id = element.get('user_id')
        knowledge_id = element.get('id')
        knowledge_name = element.get('name')
        files_ids = element.get('data', {}).get('file_ids', [])

        if user_id is None or knowledge_name is None or knowledge_id is None:
            continue

        knowledge_new_dict[user_id][knowledge_name] = {
            'knowledge_id': knowledge_id,
            'files_ids': files_ids
        }

    return knowledge_new_dict


def check_knowledge_exists(url: str, token: str, query: str = None) -> dict:
    """Check whether knowledge items exist, returning them as a nested dict.

    Uses the paginated search endpoint and paginates until all items are fetched.

    Args:
        url: Base URL of the Open WebUI instance.
        token: Bearer token for authentication.
        query: Optional search query to filter results by knowledge name.

    Returns:
        Nested dict keyed by user_id → knowledge_name → {'knowledge_id', 'files_ids'},
        or None on request failure.
    """
    endpoint = f'{url}/api/v1/knowledge/search'
    headers = {
        'Authorization': token,
        'Accept': 'application/json'
    }
    aggregated_items = []
    page = 1

    while True:
        params = {'page': page}
        if query:
            params['query'] = query

        response = get(endpoint, headers=headers, params=params)

        if response.status_code != 200:
            logger.error(f"=> Error fetching knowledge list (page {page}), status code => {response.status_code}")
            return None

        data = response.json()

        if isinstance(data, dict) and 'items' in data:
            items = data.get('items', [])
            total = data.get('total')
        elif isinstance(data, list):
            items = data
            total = None
        else:
            items = []
            total = None

        aggregated_items.extend(items)

        if total is not None:
            if len(aggregated_items) >= total:
                break
            else:
                page += 1
                continue

        if not items or len(items) < 30:
            break

        page += 1

    knowledge_dict = transform_list_of_knowledge_to_dict(aggregated_items)
    logger.info("=> Knowledge items fetched successfully")
    return knowledge_dict


def add_file_to_knowledge(url: str, token: str, knowledge_id: str, file_id: str) -> bool:
    """Add a file to an existing knowledge collection.

    Args:
        url: Base URL of the Open WebUI instance.
        token: Bearer token for authentication.
        knowledge_id: ID of the target knowledge collection.
        file_id: ID of the file to add.

    Returns:
        True if the file was added successfully, False otherwise.
    """
    url = f'{url}/api/v1/knowledge/{knowledge_id}/file/add'
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }
    data = {'file_id': file_id}
    response = post(url, headers=headers, json=data)

    if response.status_code == 200:
        logger.info("=> File added to knowledge base successfully.")
        return True
    else:
        logger.error(f"=> Error adding file to knowledge base, status code => {response.status_code}")
        return False


def create_knowledge(url: str, token: str, file_id: str, user_id: str, knowledge_name: str = 'My Generated Files') -> bool:
    """Create a knowledge collection (or reuse an existing one) and add a file to it.

    Args:
        url: Base URL of the Open WebUI instance.
        token: Bearer token for authentication.
        file_id: ID of the file to add to the collection.
        user_id: ID of the user who owns the collection.
        knowledge_name: Name of the knowledge collection.

    Returns:
        True if the file was successfully added or already present, False on error.
    """
    knowledge_dicts = check_knowledge_exists(url, token, query=knowledge_name)

    if not isinstance(knowledge_dicts, dict):
        logger.error("=> Failed to check knowledge exists")
        return False

    if knowledge_dicts.get(user_id, {}).get(knowledge_name):
        current_files = knowledge_dicts[user_id][knowledge_name].get('files_ids', [])
        if file_id in current_files:
            logger.info(f"=> File {file_id} already exists in knowledge base. No action taken.")
            return True
        else:
            logger.info(f"=> File {file_id} not found in knowledge base {knowledge_name}. Adding.")
            add_file_state = add_file_to_knowledge(
                url=url,
                token=token,
                knowledge_id=knowledge_dicts[user_id][knowledge_name]['knowledge_id'],
                file_id=file_id
            )
        logger.info("=> Knowledge base already exists. Added file to existing knowledge base of user.")
        return add_file_state
    else:
        original_url = url
        url = f'{url}/api/v1/knowledge/create'
        payload = {
            "name": knowledge_name,
            "description": "Collection of files created using GenFilesMCP",
        }
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json'
        }
        response = post(url, headers=headers, data=dumps(payload))

        if response.status_code == 200:
            logger.info("=> Knowledge base created successfully.")
            knowledge_data = response.json()
            knowledge_id = knowledge_data.get('id')
            if not knowledge_id:
                logger.error("=> No id in response after creating knowledge")
                return False

            add_file_state = add_file_to_knowledge(
                url=original_url,
                token=token,
                knowledge_id=knowledge_id,
                file_id=file_id
            )

            if add_file_state:
                logger.info("=> File added to knowledge base successfully.")
            else:
                logger.error("=> Error adding file to knowledge base")

            return True
        else:
            logger.error("=> Error creating knowledge base")
            return False

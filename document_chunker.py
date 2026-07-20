# Citirea documentelor cu false sau ceva

import os
import json
import logging
from config import CHUNK_OVERLAP, CHUNK_SIZE

logger = logging.getLogger(__name__)


def load_n_chunk_docs():
    chunk_dict_list = []
    try:
        files_to_read = os.listdir("knowledge")
    except FileNotFoundError:
        logger.warning("The 'knowledge' folder does not exist - no documents to chunk.")
        return chunk_dict_list

    for file_to_read in files_to_read:
        sub_files = os.listdir(os.path.join("knowledge", file_to_read))
        for sub_file in sub_files:
            if file_to_read == "facts" or file_to_read == "procedures":
                if sub_file.endswith(".json"):
                    registry_path = os.path.join("knowledge", file_to_read, sub_file)
                    try:
                        with open(registry_path, "r", encoding="utf-8") as f:
                            facts = json.load(f)
                    except json.JSONDecodeError:
                        logger.warning("Registry '%s' is not valid JSON - skipped.", registry_path)
                        continue
                    for fact in facts:
                        if not fact.get("always_load"):
                            doc_path = os.path.join("knowledge", file_to_read, fact.get("id") + '.md')
                            try:
                                with open(doc_path, "r", encoding="utf-8") as f2:
                                    text = f2.read()
                            except FileNotFoundError:
                                logger.warning("Document '%s' is listed in the registry but does not exist - skipped.", doc_path)
                                continue
                            words = text.split()
                            for index, chunk in enumerate(range(0, len(words), CHUNK_SIZE - CHUNK_OVERLAP)):
                                chunk_dict = {
                                    "document_id": fact.get("id"),
                                    "chunk_index": index,
                                    "content": " ".join(words[chunk:chunk + CHUNK_SIZE])
                                }
                                chunk_dict_list.append(chunk_dict)
    return chunk_dict_list
                                   
import os
import argparse
import logging
import sys
from typing import Dict, List, Optional, Set
from dotenv import load_dotenv
import json
from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient as AzureContainerClient

from services._cosmos_client import CosmosClient
from services.container_client import ContainerClient
from constants import PathConstants

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Validate files referenced in Cosmos DB exist in Azure Storage")
    parser.add_argument("--cosmosdb-endpoint", type=str, default=os.environ.get("MONGO_CONN_STRING"),
                        help="Cosmos DB endpoint or MongoDB connection string")
    parser.add_argument("--db-name", type=str, default=os.environ.get("COSMOSDB_DATABASE_NAME", "QTMGENAI"),
                        help="Database name")
    parser.add_argument("--collection-name", type=str, default=os.environ.get("COLLECTION_NAME", "Lease_Documents"),
                        help="Collection name")
    parser.add_argument("--query", type=str, default="{}",
                        help="MongoDB query in JSON format to filter documents")
    parser.add_argument("--prefix", type=str, default=PathConstants.SITE_PREFIX,
                        help=f"Prefix for files in storage (default: {PathConstants.SITE_PREFIX})")
    parser.add_argument("--max-documents", type=int, default=None,
                        help="Maximum number of documents to process from Cosmos DB")
    parser.add_argument("--verbose", action="store_true",
                        help="Show verbose output")
    return parser.parse_args()


def list_storage_files(container_client: ContainerClient, prefix: str) -> Set[str]:
    """List all files in Azure Storage with the given prefix.

    Args:
        container_client (ContainerClient): The container client
        prefix (str): Prefix for listing files    Returns:
        Set[str]: Set of file paths in Azure Storage
    """
    logger.info(f"Listing files with prefix: {prefix}")
    all_files = container_client._list_documents(prefix)
    # only get the pdf files
    all_files = [file for file in all_files if file.endswith('.pdf')]
    logger.info(f"Found {len(all_files)} PDF files with prefix '{prefix}' (file count filtered by prefix)")
    return set(all_files)


def get_cosmos_documents(cosmos_client: CosmosClient,
                         db_name: str,
                         collection_name: str,
                         query: str = "{}",
                         max_docs: Optional[int] = None) -> List[Dict]:
    """Get documents from Cosmos DB.

    Args:
        cosmos_client (CosmosClient): The Cosmos DB client
        db_name (str): Database name
        collection_name (str): Collection name
        query (str): JSON query string
        max_docs (Optional[int]): Maximum number of documents to retrieve

    Returns:
        List[Dict]: List of documents from Cosmos DB
    """
    try:
        query_dict = json.loads(query)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON query: {query}")
        query_dict = {}

    collection = cosmos_client.get_collection(db_name, collection_name)

    logger.info(f"Querying {db_name}.{collection_name} with query: {query_dict}")
    cursor = collection.find(query_dict)

    if max_docs:
        logger.info(f"Limiting to {max_docs} documents")
        docs = list(cursor.limit(max_docs))
    else:
        docs = list(cursor)

    logger.info(f"Found {len(docs)} documents in Cosmos DB")
    return docs


def extract_document_paths_from_leases(cosmos_doc: Dict) -> List[str]:
    """Extract document paths from lease documents in a Cosmos DB document.

    Args:
        cosmos_doc (Dict): A document from Cosmos DB

    Returns:
        List[str]: List of document paths referenced in the leases
    """
    document_paths = []

    # Check if this is an ExtractedSiteCollection document
    if "information" in cosmos_doc and "leases" in cosmos_doc["information"]:
        for lease in cosmos_doc["information"]["leases"]:
            if "original_documents" in lease:
                document_paths.extend(lease["original_documents"])

    return document_paths


def validate_files(
    storage_files: Set[str],
    cosmos_docs: List[Dict],
    prefix: str,
    verbose: bool = False
) -> Dict:
    """Validate that files referenced in Cosmos DB exist in Azure Storage.

    Args:
        storage_files (Set[str]): Set of file paths in Azure Storage
        cosmos_docs (List[Dict]): List of documents from Cosmos DB
        prefix (str): Prefix for files in storage
        verbose (bool): Whether to show verbose output

    Returns:
        Dict: Dictionary with validation results
    """
    results = {
        "total_documents": len(cosmos_docs),
        "documents_processed": 0,
        "documents_skipped": 0,
        "total_referenced_files": 0,
        "files_present_in_storage": 0,
        "files_missing_in_storage": 0,
        "missing_files_in_storage": []
    }

    doc_paths = []
    for doc in cosmos_docs:
        site_id = doc.get("site_id")
        if site_id is None or site_id == "unknown_site":
            results["documents_skipped"] += 1
            if verbose:
                logger.warning(f"Skipping document without site_id: {doc.get('_id', 'unknown')}")
            continue

        results["documents_processed"] += 1
        document_paths = extract_document_paths_from_leases(doc)
        doc_paths.extend(document_paths)

        if verbose:
            logger.info(f"Site ID: {site_id}, Referenced files: {len(document_paths)}")

        results["total_referenced_files"] += len(document_paths)

    # Convert to sets for efficient operations
    storage_file_paths = set(storage_files)
    doc_paths = set([path for path in doc_paths if path.startswith(prefix)])

    # Calculate files missing in storage
    missing_files = doc_paths - storage_file_paths
    results["files_missing_in_storage"] = len(missing_files)
    results["missing_files_in_storage"] = [{"path": path} for path in missing_files]

    # Calculate files present in storage
    present_files = doc_paths.intersection(storage_file_paths)
    results["files_present_in_storage"] = len(present_files)

    if verbose:
        for missing in missing_files:
            logger.warning(f"File missing in storage: {missing}")

    return results


def main():
    """Main entry point for the script."""
    # Load environment variables
    load_dotenv()

    # Parse command line arguments
    args = parse_args()

    # Get container client
    logger.info("Initializing Azure Storage container client")
    container_client = ContainerClient(
        AzureContainerClient(
            account_url=os.environ.get("SA_ACCOUNT_URL"),
            container_name=os.environ.get("SA_CONTAINER_NAME", "sites"),
            credential=DefaultAzureCredential()  # Use DefaultAzureCredential for auth
        )
    )    # List storage files
    prefix = args.prefix
    storage_files = list_storage_files(container_client, prefix)

    # Get Cosmos DB documents
    logger.info("Initializing Cosmos DB client")
    cosmos_client = CosmosClient(args.cosmosdb_endpoint)
    cosmos_docs = get_cosmos_documents(
        cosmos_client, args.db_name,
        args.collection_name,
        args.query,
        args.max_documents)

    # Validate files
    results = validate_files(storage_files, cosmos_docs, args.prefix, args.verbose)    # Print results
    logger.info("==== Validation Results ====")
    logger.info(f"Total documents in Cosmos DB: {results['total_documents']}")
    logger.info(f"Documents processed: {results['documents_processed']}")
    logger.info(f"Documents skipped (no site_id): {results['documents_skipped']}")
    logger.info(f"Total referenced files: {results['total_referenced_files']}")
    logger.info(f"Files present in storage (w/ prefix '{prefix}'): {results['files_present_in_storage']}")
    logger.info(f"Files missing in storage (w/ prefix '{prefix}'): {results['files_missing_in_storage']}")

    # Print missing files
    if results["missing_files_in_storage"]:
        logger.info("==== Files Missing in Storage ====")
        for missing in results["missing_files_in_storage"]:
            logger.info(f"Path: {missing['path']}")

    return results["files_missing_in_storage"] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

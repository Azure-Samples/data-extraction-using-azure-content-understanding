import os
import argparse
import time
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError
from pymongo import UpdateOne
from tqdm import tqdm
import logging
from services._cosmos_client import CosmosClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Transfer data from MongoDB to Cosmos DB.")
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Number of documents to process in each batch")
    parser.add_argument("--query", type=str, default="{}",
                        help="JSON query to filter documents to transfer")
    parser.add_argument("--dry-run", action="store_true",
                        help="Count documents but don't transfer them")
    parser.add_argument("--max-docs", type=int,
                        help="Maximum number of documents to transfer (useful for testing)")
    return parser.parse_args()


def process_batch(
    operations: List[UpdateOne],
    to_collection: Collection,
    pbar: tqdm
) -> Dict[str, int]:
    """Process a batch of documents using bulk write operations.

    Args:
        operations: List of bulk write operations to execute
        to_collection: Target MongoDB collection
        pbar: Progress bar to update
    Returns:
        Dict with operation statistics
    """
    stats = {
        "success": 0,
        "skipped": 0,
        "errors": 0,
        "processed": len(operations)
    }

    if not operations:
        return stats

    try:
        result = to_collection.bulk_write(operations, ordered=False)

        # Update statistics
        matched = result.matched_count
        modified = result.modified_count
        upserted = len(result.upserted_ids)

        stats["success"] = upserted + modified
        stats["skipped"] = matched - modified

        # Update progress bar
        pbar.update(len(operations))
    except BulkWriteError as bwe:
        stats["errors"] = len(bwe.details.get('writeErrors', []))
        stats["success"] = (
            bwe.details.get('nModified', 0) + bwe.details.get('nUpserted', 0)
        )
        stats["skipped"] = (
            bwe.details.get('nMatched', 0) - bwe.details.get('nModified', 0)
        )

        # Log write errors but continue processing
        logger.error(f"Bulk write error: {len(bwe.details.get('writeErrors', []))} errors occurred")
        if bwe.details.get('writeErrors'):
            for err in bwe.details.get('writeErrors')[:5]:  # Log first 5 errors
                logger.error(f"Error on document {err.get('index')}: {err.get('errmsg')}")

        # Still update the progress bar for processed docs
        pbar.update(stats["processed"])
    except Exception as e:
        stats["errors"] = len(operations)
        logger.error(f"Unexpected error processing batch: {e}")
        pbar.update(stats["processed"])

    return stats


def setup_transfer(
    from_collection: Collection,
    query: dict = None,
    max_docs: Optional[int] = None
) -> tuple:
    """Setup the transfer by checking document count and preparing cursor options.

    Args:
        from_collection (Collection): The source MongoDB collection to transfer data from.
        query (dict, optional): Filter query for documents to transfer. Defaults to None.
        max_docs (int, optional): Maximum number of documents to transfer. Defaults to None (all).

    Returns:
        tuple: (total_docs, cursor_options)
    """
    # Use empty dict if query is None
    if query is None:
        query = {}

    # Get a count of documents to transfer for the progress bar
    total_docs = from_collection.count_documents(query)
    logger.info(f"Found {total_docs} documents in source collection matching query")

    if max_docs and max_docs < total_docs:
        logger.info(f"Limiting transfer to {max_docs} documents")
        total_docs = max_docs

    # Create cursor with proper options
    cursor_options = {}
    if max_docs:
        cursor_options["limit"] = max_docs

    return total_docs, cursor_options


def create_update_operation(document: dict) -> UpdateOne:
    """Create an update operation for a document.

    Args:
        document (dict): The document to create an update operation for.

    Returns:
        UpdateOne: The update operation.
    """
    doc_id = document.get("_id")
    return UpdateOne(
        {"_id": doc_id},  # Match by _id
        {"$set": document},  # Set the document data
        upsert=True  # Insert if it doesn't exist
    )


def process_bulk_batch(
    bulk_operations: List[UpdateOne],
    to_collection: Collection,
    pbar: tqdm,
    total_stats: Dict[str, int],
    batch_start_time: float,
    total_docs: int
) -> tuple:
    """Process a batch of bulk operations and update statistics.

    Args:
        bulk_operations (List[UpdateOne]): List of bulk operations to process.
        to_collection (Collection): Target collection to update.
        pbar (tqdm): Progress bar to update.
        total_stats (Dict[str, int]): Dictionary with overall statistics to update.
        batch_start_time (float): Start time of the batch for performance reporting.
        total_docs (int): Total number of documents to process for progress reporting.

    Returns:
        tuple: (updated_total_stats, new_batch_start_time, empty_bulk_operations_list)
    """
    batch_stats = process_batch(bulk_operations, to_collection, pbar)

    # Update overall statistics
    total_stats["processed"] += batch_stats["processed"]
    total_stats["success"] += batch_stats["success"]
    total_stats["skipped"] += batch_stats["skipped"]
    total_stats["errors"] += batch_stats["errors"]

    # Log progress and performance metrics
    batch_end_time = time.time()
    batch_duration = batch_end_time - batch_start_time
    docs_per_second = len(bulk_operations) / batch_duration if batch_duration > 0 else 0

    if total_stats["processed"] % 10000 == 0 or batch_stats["errors"] > 0:
        logger.info(
            f"Progress: {total_stats['processed']}/{total_docs} documents | "
            f"Speed: {docs_per_second:.2f} docs/sec | "
            f"Success: {total_stats['success']} | Skipped: {total_stats['skipped']} | "
            f"Errors: {total_stats['errors']}"
        )

    return total_stats, batch_end_time, []


def log_final_statistics(total_stats: Dict[str, int], start_time: float) -> None:
    """Log final transfer statistics.

    Args:
        total_stats (Dict[str, int]): Dictionary with overall statistics.
        start_time (float): Start time of the transfer.
    """
    end_time = time.time()
    total_duration = end_time - start_time
    avg_speed = total_stats["processed"] / total_duration if total_duration > 0 else 0

    logger.info(f"Transfer complete: {total_stats['processed']} documents processed in {total_duration:.2f} seconds")
    logger.info(f"Average speed: {avg_speed:.2f} documents/second")
    logger.info(
        f"Success: {total_stats['success']}, "
        f"Skipped: {total_stats['skipped']}, "
        f"Errors: {total_stats['errors']}"
    )


def main(
    from_collection: Collection,
    to_collection: Collection,
    batch_size: int = 100,
    query: dict = None,
    dry_run: bool = False,
    max_docs: Optional[int] = None
):
    """Transfer documents from one MongoDB collection to another using bulk operations.

    Args:
        from_collection (Collection): The source MongoDB collection to transfer data from.
        to_collection (Collection): The target MongoDB collection to transfer data to.
        batch_size (int, optional): Number of documents to process in each batch. Defaults to 100.
        query (dict, optional): Filter query for documents to transfer. Defaults to None.
        dry_run (bool, optional): If True, only count documents without transferring. Defaults to False.
        max_docs (int, optional): Maximum number of documents to transfer. Defaults to None (all).
    """
    # Setup the transfer
    total_docs, cursor_options = setup_transfer(from_collection, query, max_docs)

    if dry_run:
        logger.info("Dry run mode - no documents will be transferred")
        return

    if total_docs == 0:
        logger.info("No documents to transfer - exiting")
        return

    # Get cursor
    cursor = from_collection.find(query, batch_size=batch_size, **cursor_options)

    # Initialize counters
    total_stats = {
        "processed": 0,
        "success": 0,
        "skipped": 0,
        "errors": 0
    }

    # Optimize bulk batch size based on document size/complexity
    bulk_batch_size = min(1000, batch_size)
    bulk_operations = []

    # Track timing for performance reporting
    start_time = time.time()
    batch_start_time = start_time

    # Create a progress bar
    with tqdm(total=total_docs, desc="Transferring documents") as pbar:
        for document in cursor:
            try:
                # Create an update operation for this document
                bulk_operations.append(create_update_operation(document))

                # Execute bulk operation when batch size is reached
                if len(bulk_operations) >= bulk_batch_size:
                    total_stats, batch_start_time, bulk_operations = process_bulk_batch(
                        bulk_operations, to_collection, pbar, total_stats,
                        batch_start_time, total_docs
                    )

            except Exception as e:
                total_stats["errors"] += 1
                logger.error(f"Error processing document: {e}")

        # Process any remaining operations in the final batch
        if bulk_operations:
            total_stats, _, _ = process_bulk_batch(
                bulk_operations, to_collection, pbar, total_stats,
                batch_start_time, total_docs
            )

    # Calculate and log final statistics
    log_final_statistics(total_stats, start_time)


if __name__ == "__main__":
    start_time = time.time()
    script_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"Starting MongoDB data transfer at {script_start}")
    load_dotenv()
    args = _parse_args()

    mongo_conn_string = os.environ.get("MONGO_CONN_STRING")
    from_database_name = os.environ.get("FROM_DATABASE_NAME")
    to_database_name = os.environ.get("TO_DATABASE_NAME")
    from_collection_name = os.environ.get("FROM_COLLECTION_NAME")
    to_collection_name = os.environ.get("TO_COLLECTION_NAME")

    # check that all env vars are set correctly
    if not all([mongo_conn_string, from_database_name, to_database_name, from_collection_name, to_collection_name]):
        raise ValueError("One or more environment variables are not set correctly.")

    # Parse the query argument if provided
    query = {}
    if args.query:
        try:
            import json
            query = json.loads(args.query)
            logger.info(f"Using query filter: {query}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON query: {args.query}")
            logger.info("Using empty query instead")

    # Log execution parameters
    logger.info(f"Batch size: {args.batch_size}")
    if args.max_docs:
        logger.info(f"Max docs: {args.max_docs}")
    if args.dry_run:
        logger.info("Mode: DRY RUN (no data will be transferred)")
    else:
        logger.info("Mode: LIVE (data will be transferred)")

    try:
        cosmos_client = CosmosClient(mongo_conn_string)
        from_collection = cosmos_client.get_collection(from_database_name, from_collection_name)
        to_collection = cosmos_client.get_collection(to_database_name, to_collection_name)

        # Log collection information
        logger.info(f"Source collection: {from_database_name}.{from_collection_name}")
        logger.info(f"Target collection: {to_database_name}.{to_collection_name}")

        main(
            from_collection=from_collection,
            to_collection=to_collection,
            batch_size=args.batch_size,
            query=query,
            dry_run=args.dry_run,
            max_docs=args.max_docs
        )
    except Exception as e:
        logger.error(f"Fatal error during data transfer: {e}", exc_info=True)
    finally:
        script_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_runtime = time.time() - start_time
        logger.info(f"Data transfer script completed at {script_end}")
        logger.info(f"Total runtime: {total_runtime:.2f} seconds ({total_runtime/60:.2f} minutes)")

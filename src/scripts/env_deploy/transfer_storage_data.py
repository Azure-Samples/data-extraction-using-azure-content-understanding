import os
import argparse
import time
import sys
import logging
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv
from multiprocessing.pool import ThreadPool
from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient as AzureContainerClient
from services.container_client import ContainerClient
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

_SITES_PREFIX = "Sites/"
_MLA_PREFIX = "MLA/"


def _parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Transfer data between Azure Storage containers.")
    parser.add_argument("--prefix", type=str, default=_SITES_PREFIX,
                        help=f"Prefix filter for blobs to transfer. Default: {_SITES_PREFIX}")
    parser.add_argument("--threads", type=int, default=10,
                        help="Number of concurrent threads for transfer. Default: 10")
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Number of files to process in each batch. Default: 100")
    parser.add_argument("--dry-run", action="store_true",
                        help="Count blobs but don't transfer them")
    parser.add_argument("--max-files", type=int,
                        help="Maximum number of files to transfer (useful for testing)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite files in destination even if they exist")
    return parser.parse_args()


def _download_and_transfer_file(
    from_container_client: ContainerClient,
    to_container_client: ContainerClient,
    file_path: str,
    overwrite: bool = False
) -> Dict[str, int]:
    """Download a file from one container and upload it to another.

    Args:
        from_container_client: Source container client
        to_container_client: Destination container client
        file_path: Path of the file to transfer
        overwrite: Whether to overwrite existing files in destination

    Returns:
        Dictionary with operation results
    """
    result = {"success": 0, "skipped": 0, "error": 0}

    try:
        # Check if file exists in destination
        file_exists = to_container_client.file_exists(file_path)

        if file_exists and not overwrite:
            result["skipped"] = 1
            return result
        # Download file from source
        content, metadata = from_container_client.download_file(file_path)
        to_container_client.upload_document(content, file_path, metadata)
        result["success"] = 1

    except Exception as e:
        logger.error(f"Error transferring {file_path}: {str(e)}")
        result["error"] = 1

    return result


def process_batch(
    batch_files: list,
    from_container_client: ContainerClient,
    to_container_client: ContainerClient,
    overwrite: bool,
    pbar: tqdm,
    threads: int = 10
) -> Dict[str, int]:
    """Process a batch of files by transferring them in parallel.

    Args:
        batch_files: List of file paths to transfer
        from_container_client: Source container client
        to_container_client: Destination container client
        overwrite: Whether to overwrite existing files in destination
        pbar: Progress bar to update
        threads: Number of concurrent threads to use

    Returns:
        Dict with operation statistics
    """
    stats = {
        "success": 0,
        "skipped": 0,
        "errors": 0,
        "processed": len(batch_files)
    }

    if not batch_files:
        return stats

    parameters = [
        (from_container_client, to_container_client, file_path, overwrite)
        for file_path in batch_files
    ]

    try:
        # Use the threads parameter instead of hardcoded value
        threads_to_use = min(len(batch_files), threads)
        with ThreadPool(processes=threads_to_use) as pool:
            results = pool.starmap(_download_and_transfer_file, parameters)

        # Aggregate results
        for result in results:
            stats["success"] += result.get("success", 0)
            stats["skipped"] += result.get("skipped", 0)
            stats["errors"] += result.get("error", 0)

        # Update progress bar
        pbar.update(len(batch_files))

    except Exception as e:
        stats["errors"] = len(batch_files)
        logger.error(f"Error processing batch: {str(e)}")
        pbar.update(len(batch_files))

    return stats


def main(
    from_container_client: ContainerClient,
    to_container_client: ContainerClient,
    batch_size: int = 100,
    threads: int = 10,
    dry_run: bool = False,
    max_files: Optional[int] = None,
    overwrite: bool = False
):
    """Transfer files from one Azure storage container to another using parallel batch processing.

    Args:
        from_container_client: Source container client
        to_container_client: Destination container client
        batch_size: Number of files to process in each batch
        threads: Number of concurrent threads for transfer
        dry_run: If True, only count files without transferring
        max_files: Maximum number of files to transfer
        overwrite: Whether to overwrite existing files in destination
    """
    logger.info("Starting data transfer...")

    # List all documents to transfer
    all_prefixes = [_SITES_PREFIX, _MLA_PREFIX]
    from_documents = []

    for prefix in all_prefixes:
        logger.info(f"Listing files with prefix: {prefix}")
        prefix_files = from_container_client._list_documents(prefix)
        logger.info(f"Found {len(prefix_files)} files with prefix {prefix}")
        from_documents.extend(prefix_files)

    total_files = len(from_documents)
    logger.info(f"Found total of {total_files} files to transfer")

    if max_files and max_files < total_files:
        logger.info(f"Limiting transfer to {max_files} files")
        from_documents = from_documents[:max_files]
        total_files = len(from_documents)

    if dry_run:
        logger.info("Dry run mode - no files will be transferred")
        return

    if total_files == 0:
        logger.info("No files to transfer - exiting")
        return

    # Initialize counters and timing
    total_processed = 0
    total_success = 0
    total_skipped = 0
    total_errors = 0

    start_time = time.time()
    batch_start_time = start_time    # Create a progress bar
    with tqdm(total=total_files, desc="Transferring files", unit="file") as pbar:
        # Process files in batches
        for i in range(0, total_files, batch_size):
            batch_files = from_documents[i:i + batch_size]

            batch_stats = process_batch(
                batch_files=batch_files,
                from_container_client=from_container_client,
                to_container_client=to_container_client,
                overwrite=overwrite,
                pbar=pbar,
                threads=threads
            )

            # Update overall statistics
            total_processed += batch_stats["processed"]
            total_success += batch_stats["success"]
            total_skipped += batch_stats["skipped"]
            total_errors += batch_stats["errors"]

            # Log progress and performance metrics
            batch_end_time = time.time()
            batch_duration = batch_end_time - batch_start_time
            files_per_second = len(batch_files) / batch_duration if batch_duration > 0 else 0

            if i % 1000 == 0 or batch_stats["errors"] > 0:
                logger.info(
                    f"Progress: {total_processed}/{total_files} files | "
                    f"Speed: {files_per_second:.2f} files/sec | "
                    f"Success: {total_success} | Skipped: {total_skipped} | Errors: {total_errors}"
                )

            # Reset for next batch
            batch_start_time = batch_end_time

    # Calculate and log final statistics
    end_time = time.time()
    total_duration = end_time - start_time
    avg_speed = total_processed / total_duration if total_duration > 0 else 0

    logger.info(f"Transfer complete: {total_processed} files processed in {total_duration:.2f} seconds")
    logger.info(f"Average speed: {avg_speed:.2f} files/second")
    logger.info(f"Success: {total_success}, Skipped: {total_skipped}, Errors: {total_errors}")


if __name__ == "__main__":
    start_time = time.time()
    script_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"Starting Storage data transfer at {script_start}")
    load_dotenv()
    args = _parse_args()

    # Check environment variables
    required_env_vars = ["FROM_ACCOUNT_URL", "FROM_CONTAINER_NAME", "TO_ACCOUNT_URL", "TO_CONTAINER_NAME"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    # Log execution parameters
    logger.info(f"Prefix: {args.prefix}")
    logger.info(f"Threads: {args.threads}")
    logger.info(f"Batch size: {args.batch_size}")
    if args.max_files:
        logger.info(f"Max files: {args.max_files}")
    if args.dry_run:
        logger.info("Mode: DRY RUN (no files will be transferred)")
    else:
        logger.info("Mode: LIVE (files will be transferred)")
    if args.overwrite:
        logger.info("Files will be overwritten if they exist in the destination")

    try:
        from_account_url = os.getenv("FROM_ACCOUNT_URL")
        from_container_name = os.getenv("FROM_CONTAINER_NAME")
        to_account_url = os.getenv("TO_ACCOUNT_URL")
        to_container_name = os.getenv("TO_CONTAINER_NAME")

        credentials = DefaultAzureCredential()
        from_container_client = AzureContainerClient(
            account_url=from_account_url,
            container_name=from_container_name,
            credential=credentials
        )
        to_container_client = AzureContainerClient(
            account_url=to_account_url,
            container_name=to_container_name,
            credential=credentials
        )

        # Log container information
        logger.info(f"Source container: {from_container_name}")
        logger.info(f"Target container: {to_container_name}")
        main(
            from_container_client=ContainerClient(from_container_client),
            to_container_client=ContainerClient(to_container_client),
            batch_size=args.batch_size,
            threads=args.threads,
            dry_run=args.dry_run,
            max_files=args.max_files,
            overwrite=args.overwrite
        )

    except Exception as e:
        logger.error(f"Fatal error during data transfer: {e}", exc_info=True)
        sys.exit(1)

    finally:
        script_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_runtime = time.time() - start_time
        logger.info(f"Data transfer script completed at {script_end}")
        logger.info(f"Total runtime: {total_runtime:.2f} seconds ({total_runtime/60:.2f} minutes)")

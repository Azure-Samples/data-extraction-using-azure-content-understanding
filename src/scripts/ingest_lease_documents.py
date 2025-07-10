import os
import logging
import json
from datetime import datetime
import argparse
from typing import Union

from tqdm import tqdm
from configs import get_app_config_manager
from services.container_client import get_container_client
from services.ingest_lease_documents_service import IngestionSiteLeaseService
from services.ingest_config_management_service import IngestConfigManagementService
from services.azure_content_understanding_client import AzureContentUnderstandingClient
from controllers.ingest_lease_documents_controller import IngestLeaseDocumentsController
from utils.constants import AZURE_AI_CONTENT_UNDERSTANDING_USER_AGENT
from models.ingestion_models import (
    MLAIngestDocumentRequest,
    SiteIngestDocumentRequest
)
from constants import PathConstants


class TqdmLoggingHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        tqdm.write(msg)


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[TqdmLoggingHandler()])


_BASE_DIRECTORY_PATH = "lease_documents_dataset/"
_SITES_BASE_PATH = PathConstants.SITE_PREFIX
_MLA_BASE_PATH = PathConstants.MLA_PREFIX
_SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
_BATCH_SIZE = 10
_PDF_EXTENSION = ".pdf"


def _parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Ingest lease documents.")
    parser.add_argument(
        "--environment",
        type=str,
        default="local",
        help="Environment to run the script in (default: local)"
    )
    parser.add_argument(
        "--refresh-data",
        action="store_true",
        help="Refresh data in the database (default: False)"
    )
    parser.add_argument(
        "--config-name",
        type=str,
        default="lesa_config",
        help="Configuration name to use for document ingestion (default: lesa_config)"
    )
    parser.add_argument(
        "--config-version",
        type=str,
        default="v2",
        help="Configuration version to use for document ingestion (default: v2)"
    )

    return parser.parse_args()


def _build_dataset_path(base_directory_path: str, storage_account_name: str, container_name: str) -> str:
    return os.path.join(
        _SRC_DIR,
        base_directory_path,
        storage_account_name,
        container_name
    )


def _get_content_and_metadata_from_file_path(
    file_path: str
) -> tuple[bytes, dict]:
    if not file_path.endswith(".pdf"):
        return

    metadata_file_path = file_path.replace(".pdf", ".json")

    content: bytes = None
    with open(file_path, 'rb') as file:
        content = file.read()

    metadata: dict = None
    with open(metadata_file_path, 'r') as file:
        metadata = json.load(file)

    return content, metadata


def _process_sites(sites_path: str) -> list[SiteIngestDocumentRequest]:
    for market in os.listdir(sites_path):
        market_directory_path = os.path.join(sites_path, market)
        for site_id in os.listdir(market_directory_path):
            site_directory_path = os.path.join(market_directory_path, site_id)
            for lease_id in os.listdir(site_directory_path):
                lease_directory_path = os.path.join(site_directory_path, lease_id)
                for file_name in os.listdir(lease_directory_path):
                    file_path = os.path.join(lease_directory_path, file_name)
                    result = _get_content_and_metadata_from_file_path(
                        file_path
                    )

                    if result is None:
                        continue

                    content, metadata = result
                    date_of_document = datetime.strptime(
                        metadata["date"], "%Y-%m-%d",
                    ).date()
                    yield SiteIngestDocumentRequest(
                        id=site_id.upper(),
                        market=market.upper(),
                        lease_id=lease_id,
                        filename=file_name,
                        file_bytes=content,
                        date_of_document=date_of_document
                    )


def _process_mla(mla_path: str) -> list[MLAIngestDocumentRequest]:
    for mla_id in os.listdir(mla_path):
        mla_id_path = os.path.join(mla_path, mla_id)
        for file_name in os.listdir(mla_id_path):
            file_path = os.path.join(mla_id_path, file_name)
            result = _get_content_and_metadata_from_file_path(
                file_path
            )

            if result is None:
                continue

            content, metadata = result
            date_of_document = datetime.strptime(
                metadata["date"], "%Y-%m-%d",
            ).date()
            yield MLAIngestDocumentRequest(
                id=mla_id.upper(),
                filename=file_name,
                file_bytes=content,
                date_of_document=date_of_document
            )


def _try_run_batch(
    controller: IngestLeaseDocumentsController,
    batch: list[Union[MLAIngestDocumentRequest, SiteIngestDocumentRequest]],
    config_name: str,
    config_version: str,
    remaining: bool = False
):
    if (len(batch) >= _BATCH_SIZE) or (remaining and len(batch) > 0):
        try:
            controller.ingest_documents(
                config_name,
                config_version,
                batch
            )
        except Exception as e:
            logging.error(f"Error processing batch: {e}")
        finally:
            batch.clear()  # Use clear() to empty the list in place


def main(refresh_data: bool, config_name: str, config_version: str, use_default_config: bool = False):
    """Main function to ingest lease documents."""
    environment_config = get_app_config_manager(True).hydrate_config()
    ingestion_audit_site_lease_service = IngestionSiteLeaseService.from_environment_config(environment_config)
    container_client = get_container_client(environment_config)
    environment_config = get_app_config_manager().hydrate_config()
    ingestion_configuration_management_service = IngestConfigManagementService.from_environment_config(
        environment_config
    )

    content_understanding_client = AzureContentUnderstandingClient(
        endpoint=environment_config.content_understanding.endpoint.value,
        subscription_key=environment_config.content_understanding.subscription_key.value,
        x_ms_useragent=AZURE_AI_CONTENT_UNDERSTANDING_USER_AGENT
    )
    controller = IngestLeaseDocumentsController(
        content_understanding_client,
        ingestion_audit_site_lease_service,
        ingestion_configuration_management_service
    )

    storage_account_url = environment_config.blob_storage.account_url.value
    container_name = environment_config.blob_storage.container_name.value
    storage_account_name = storage_account_url.split(".")[0].split("//")[1]

    local_folder_path = _build_dataset_path(
        _BASE_DIRECTORY_PATH,
        storage_account_name,
        container_name
    )

    if not os.path.exists(local_folder_path):
        refresh_data = True
        os.makedirs(local_folder_path, exist_ok=True)

    if refresh_data:
        logging.info("Downloading lease documents from Azure Blob Storage...")
        container_client.download_files(
            _SITES_BASE_PATH,
            local_folder_path,
            _PDF_EXTENSION
        )
        container_client.download_files(
            _MLA_BASE_PATH,
            local_folder_path,
            _PDF_EXTENSION
        )

    if use_default_config:
        config_name = environment_config.default_ingest_config.name.value
        config_version = environment_config.default_ingest_config.version.value

    # Process documents and ingest them
    batch: list[MLAIngestDocumentRequest | SiteIngestDocumentRequest] = []
    for doc_type in os.listdir(local_folder_path):
        doc_type_directory_path = os.path.join(local_folder_path, doc_type)
        if doc_type == _MLA_BASE_PATH:
            mla_results = list(_process_mla(doc_type_directory_path))
            for result in tqdm(mla_results):
                batch.append(result)
                _try_run_batch(
                    controller,
                    batch,
                    config_name,
                    config_version
                )
            _try_run_batch(
                controller,
                batch,
                config_name,
                config_version,
                remaining=True
            )
        elif doc_type == _SITES_BASE_PATH:
            site_results = list(_process_sites(doc_type_directory_path))
            for result in tqdm(site_results):
                batch.append(result)
                _try_run_batch(
                    controller,
                    batch,
                    config_name,
                    config_version,
                )
            _try_run_batch(
                controller,
                batch,
                config_name,
                config_version,
                remaining=True
            )
        else:
            logging.warning(f"Unknown document type: {doc_type}")
            continue


if __name__ == "__main__":
    args = _parse_args()
    environment = args.environment
    refresh_data = args.refresh_data
    config_name = args.config_name
    config_version = args.config_version
    os.environ["ENVIRONMENT"] = environment

    use_default_config = False
    if (config_version.lower() == "none" and config_name.lower() == "none") or \
       (config_version == "" and config_name == ""):
        use_default_config = True
        logging.info("No config name or version provided. Using default config.")
    elif (config_version != "" and config_name != "") or \
         (config_version.lower() != "none" and config_name.lower() != "none"):
        logging.info(f"Using config {config_name}:{config_version}")
    else:
        raise ValueError("Config name and version must be provided together or not at all.")

    main(
        refresh_data=refresh_data,
        config_name=config_name,
        config_version=config_version,
        use_default_config=use_default_config
    )

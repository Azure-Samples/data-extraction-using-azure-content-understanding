import os
import click
import asyncio
import logging
import json
from models.data_collection_config import UnityCatalogCollectionRow
from services.llm_request_manager import get_llm_request_manager
from services.unity_catalog_executor import get_unity_catalog_executor
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

_ASSETS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "assets"
)
system_prompt: str
with open(os.path.join(_ASSETS_PATH, "generate_qa_system_message.txt"), 'r') as f:
    system_prompt = f.read()


async def _generate_queries(config_dir, configs, output_file, sites, executor):
    llm_request_manager = get_llm_request_manager()
    results = []
    contexts = []
    for config in configs:
        with open(os.path.join(config_dir, config)) as f:
            defs = json.load(f)

        collection_rows = []
        for row_def in defs["collection_rows"]:
            collection_rows.append(UnityCatalogCollectionRow(
                catalog=row_def["catalog"],
                query=row_def["query"],
                partition_key=row_def["partition_key"],
                field_schema=row_def["field_schema"]
            ))

        for site_id in sites:
            output = {"site_id": site_id, "lease_info": []}

            for collection_row in collection_rows:
                response = executor.execute(collection_row, site_id)

                for key, val in response.items():
                    lease_info = {}
                    for returned_row in val:
                        for row_key, row_val in returned_row.items():
                            logging.info("Name: {}\tValue: {}".format(row_key, row_val.value))
                            lease_info[row_key] = row_val.value
                    output["lease_info"].append(lease_info)

            output_str = json.dumps(output, indent=2)
            response = await llm_request_manager.answer_general_question(
                system_message=system_prompt,
                user_message=output_str
            )

            logging.info(response)
            results.append(response)
            contexts.append(output_str)

    with open(output_file, 'w') as f:
        for result, context in zip(results, contexts):
            print(result)

            q_loc = result.find("Question:")
            a_loc = result.find("Answer:")
            if q_loc != -1 and a_loc != -1:
                question = result[q_loc + 9 : a_loc].strip()
                answer = result[a_loc + 7:].strip()

                output = {"Question": question, "Answer": answer, "context": context}
                f.write(json.dumps(output) + "\n")


@click.group()
def cli():
    """CLI for the generation package."""
    pass


@cli.command()
@click.option(
    "--config_dir",
    type=str,
    default="evaluation/ingest_configs",
    help="Directory where configuration files are located"
)
@click.option(
    "--configs",
    type=str,
    default="amounts,assignment,dates,insurance,modification,termination",
    help="Comma separated list of configs to use"
)
@click.option(
    "--site_list_file",
    type=str,
    default="site_list_small.txt",
    help="File containing list of sites to generate questions for"
)
@click.option(
    "--output_file",
    type=str,
    default="evaluation/data/qatest.jsonl",
    help="Name of output file"
)
def generate(
    config_dir: str,
    configs: str,
    site_list_file: str,
    output_file: str
):
    """Generate questions and responses.

    Args:
        config_dir (str): Directory where configuration files are located.
        configs (str): Comma separated list of configs to use.
        site_list_file (str): Filename with list of site IDs to use.
        output_file (str): Name of output file.
    """
    configs = [config + ".json" for config in configs.split(",")]

    sites = []
    executor = get_unity_catalog_executor()

    with open(os.path.join(_ASSETS_PATH, site_list_file), 'r') as f:
        for line in f.readlines():
            sites.append(line.strip())

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_generate_queries(config_dir, configs, output_file, sites, executor))


if __name__ == "__main__":
    cli()

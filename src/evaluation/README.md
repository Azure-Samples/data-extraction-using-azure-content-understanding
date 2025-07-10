# Evaluation Program

## Overview

The Evaluation Program is designed to run evaluations on datasets using various configurations. It leverages Azure AI Foundry for data management and evaluation and the function app for config management and inference. This document provides instructions on how to set up and run the evaluation program.

## Table of Contents

- [Evaluation Program](#evaluation-program)
  - [Overview](#overview)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Evaluation](#running-the-evaluation)
  - [Evaluation Steps](#evaluation-steps)
  - [Logging](#logging)
  - [Uploading a New Metric to Azure Foundry](#uploading-a-new-metric-to-azure-foundry)
    - [Steps to Upload a New Evaluator](#steps-to-upload-a-new-evaluator)
    - [Triggering the Upload in VS Code](#triggering-the-upload-in-vs-code)
    - [Notes](#notes)
    - [Archiving an unused evaluator](#archiving-an-unused-evaluator)

## Prerequisites

Before you begin, ensure you have met the following requirements:

- You have an Azure account with the necessary permissions to access Azure services.
- You have installed the Azure CLI and are logged in (`az login`).
- You have installed `pip` for managing Python packages.

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/your-repo/qtm-lesa-core.git
    cd qtm-lesa-core
    ```

2. Create and activate a virtual environment:

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:

    ```sh
    pip install -r requirements.txt
    pip install -r requirements_eval.txt
    ```

## Configuration

1. Create a `.env` file in the `src` directory and add the necessary environment variables:

    ```env
    AZURE_FOUNDRY_CONNECTION_STRING=your_connection_string
    CONNECTION_NAME="qtmNpeGenAIWu2Oai1"
    GPT_DEPLOYMENT_NAME="gpt-4o"
    OPENAI_API_VERSION="2023-05-15"
    ```
    
    CONNECTION_NAME, GPT_DEPLOYMENT_NAME, and OPENAI_API_VERSION can be changed but these are the recommended values.

## Running the Evaluation

1. Run from debugger - Evaluation Framework or Run the evaluation program using the following command:

    ```sh
    cd src
    python -m evaluation.src.main eval --environment <your-environment> --dataset-name <your-dataset-name> --dataset-version <your-dataset-version> --config-name <your-config-name or "none"> --config-version <your-config-version or "none"> --bearer-token <your-bearer-token>
    ```

    Replace `<your-environment>`, `<your-dataset-name>`, `<your-dataset-version>`, `<your-ingest-config-file-name>` with the appropriate values.

    `<your-environment>` - Indicates whether you are running the tests against local function chat endpoint or running against a dev or prod environment. Ensure your endpoint is set correcty in evaluation/config/config.yml

    `<your-dataset-name>`, `<your-dataset-version>` - Upload your dataset in Azure Foundry - Data + indexes. Your dataset should be in jsonl and should include "Question" and "Answer". Use the uploaded file Name and version. Dataset: GT_M1, Version: 1 has set of 42 questions that covers all active and key clauses questions for a single site that you can use for quickly validating any functionally changes.


    `<your-config-name>`, `<your-config-version>` - Specify the ingest configuration name and version to use for evaluation. These configurations define the prompt and fields to extract during evaluation. If you want to use the default ingest configuration defined in your environment settings, set these parameters to `"none"` or omit them. Ensure the configuration has been ingested.

    `<your-bearer-token>` - Your bearer token is required when running evaluations against the dev or prod environments, or locally if authentication is enabled. To obtain your bearer token, navigate to the Network Copilot URL corresponding to the environment you intend to use. Locate the LESA card, right-click, and select **Inspect**. In the developer tools panel, navigate to the **Network** tab and locate the **leasingAiAuthCheck** request under the Fetch/XHR requests. Within the request details, find the **Authorization** header and copy its value (excluding the "Bearer" prefix). The interface for retrieving the bearer token should resemble the image below.

    ![Bearer token inspect element](../../documentation/assets/bearer-token-inspect-element.png)

## Evaluation Steps

The evaluation process involves the following steps:

1. **Load Configuration**: The program loads the configuration settings based on the specified environment (local, dev, prod).
2. **Initialize Services**: The program initializes the necessary services, including `DataManager`, `ApiManager`, and `EvaluationManager`.
3. **Load Ingest Configuration**: The program loads the ingest configuration file specified by the user.
4. **Run Orchestrator**: The `Orchestrator` service is used to manage the evaluation process. It coordinates between the `DataManager`, `ApiManager`, and `EvaluationManager` to perform the evaluation.
5. **Execute Evaluation**: The orchestrator runs the evaluation on the specified dataset and version, using the provided configuration settings.
6. **Save Results**: The results of the evaluation are saved to foundry.


## Logging

The logging configuration is defined in the `logger_config.yaml` file. By default, it will log messages from the application at the `INFO` level and suppress logs from external dependencies unless they are errors.


## Uploading a New Metric to Azure Foundry

This guide explains how to upload a new evaluator (metric) to Azure Foundry and trigger the process using the "Evaluation: Upload Evaluator" option in VS Code.

### Steps to Upload a New Evaluator

1. **Prepare the Evaluator**:
   - Create a folder for your evaluator under the `evaluators` directory.
   - Ensure the folder contains all necessary files for the evaluator.

2. **Run the Upload Command**:
   - Open a terminal in the project root.
   - Use the following command to upload the evaluator:
     ```bash
     python src/evaluation/src/main.py upload-evaluator \
       --evaluator-name <EVALUATOR_NAME> \
       --evaluator-description "<EVALUATOR_DESCRIPTION>" \
       --evaluator-folder-name <EVALUATOR_FOLDER_NAME>
     ```
   - Replace `<EVALUATOR_NAME>`, `<EVALUATOR_DESCRIPTION>`, and `<EVALUATOR_FOLDER_NAME>` with appropriate values.

3. **Verify the Upload**:
   - Check the Azure Foundry registry to ensure the evaluator has been uploaded successfully.

### Triggering the Upload in VS Code

1. Open the **Run and Debug** panel in VS Code.
2. Select the `Evaluation: Upload Evaluator` configuration.
3. Click the green play button to start the process.
4. Provide the required inputs (evaluator name, description, and folder name) when prompted.

### Notes

- Ensure the `AZURE_FOUNDRY_CONNECTION_STRING` & `CONNECTION_NAME` environment variable is set before running the command.

### Archiving an unused evaluator

To archive an evaluator that was just created for testing purposes or is no longer used:

1. Open the **Run and Debug** panel in VS Code.
2. Select the `Evaluation: Archive Evaluator` launch configuration.
3. Click the green play button to start the process.
4. Provide the required inputs (evaluator name, latest version) when prompted.

If you archive something accidentally, or want to unarchive an archived evaluator, there's also a task provided under `Evaluation: Restore Archived Evaluator`.

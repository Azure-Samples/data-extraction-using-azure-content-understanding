# Using the Azure AI Content Understanding classifier

## Background

We would like to be able to use the [classifier API](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/concepts/classifier) available in the `2025-05-15-preview` release of Azure AI Content Understanding (CU) to identify different categories of documents within a single input file, and selectively run our analyzer on only the subdocuments that we want to extract information from.

Note that we are already using the [existing analyzer feature](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/document/overview) of CU to extract key fields from the raw  documents, per [our architecture document](architecture.md).
The classifier API builds on this concept to automatically categorize documents in a file based on a user-provided description;
it can then optionally apply an analyzer to each of the categorized documents based on the classifier schema to extract fields in the same way that we currently are only able to do at the full document level.
See [the classifier REST API documentation](https://learn.microsoft.com/en-us/rest/api/contentunderstanding/content-classifiers/classify?view=rest-contentunderstanding-2025-05-01-preview&tabs=HTTP) for more information and example usage;
this is also covered in [the appendix](#appendix).

This design document is scoped to updating our application to support using the CU classifier feature;
it does **not** cover creating, testing, and deploying the final classifier schema for this use case.

## Configuration updates

We will have to specify the classifier ID in our JSON configuration, to be used at ingestion and inference time.

```json
{
  "_id": "test_config-v1",
  "name": "test_config",
  "version": "v1",
  "prompt": "You are a helpful assistant...",
  "extraction_config_hash": "<hash>",
  "collection_rows": [
    {
      "data_type": "LeaseAgreement",
      "field_schema": [...],
      "analyzer_id": "test-analyzer",
      "classifier": {
        "enabled": true,
        "classifier_id": "test-classifier"
      }
    }
  ]
}
```

This will also include a feature flag to enable/disable the use of this feature based on need.

## Code updates

Required code updates to update our current application ingestion process to support the use of the CU classifier feature:

1. Update config hashing process to include classifier ID.
2. Update content understanding client to support classification API calls (include classifier ID in call to content understanding if the classifier feature flag is enabled).
3. Update ingestion controller to use classifier settings from config and call appropriate method from the CU client.
4. Transform the [result of the CU classifier operation](#sample-cu-classifier-result) to the the document format that we'll save to CosmosDB.
This will stay pretty much the same as we currently have it -
all of the extracted fields from the document categories that included an analyzer in the classifier schema will be added to the `fields` array for that particular `document_id` in the document (named by `{collectionID}-{hash of analyzer config + classifier ID}.json`), with the addition of the classified `category`, `subdocument_start_page`, and `subdocument_end_page` as a property of each `field` item.
Note that these new properties will be included in the CosmosDB document for debugging purposes, but will not be part of the context passed to the LLM.

### Resulting CosmosDB document example

```json
{
  "_id": "Collection1-<hash>",
  "is_locked": false,
  "unlock_unix_timestamp": 0,
  "collection_id": "Collection1",
  "config_id": "test_config-v1",
  "extraction_config_hash": "<hash>",
  "information": {
    "entities": [
      {
        "lease_id": "Lease1",
        "original_documents": [
          "Lease1.pdf"
        ],
        "markdowns": [
          "Lease1.md"
        ],
        "fields": {
          "monthly_rent": [
            {
              "type": "integer",
              "valueInteger": 2000,
              "spans": [...],
              "confidence": 0.524,
              "source": "D(1,3.1131,5.8454,7.3705,5.8454,7.3705,6.0542,3.1131,6.0542)",
              "date_of_document": "2023-02-01",
              "markdown": "Lease1.md",
              "document": "Lease1.pdf",
              "category": "property_lease"
            },
            ...
          ],
        },
      }
    ],
            ...
  },
}

```

## Appendix

### Currently available CU classifier API methods

```bash
### Create a classifier
# @name createClassifier
curl -i -X PUT "{{AZURE_AI_SERVICE_ENDPOINT}}/contentunderstanding/classifiers/{{CLASSIFIER_ID}}?api-version=2025-05-01-preview"
  -H "Ocp-Apim-Subscription-Key: {{AZURE_AI_SERVICE_KEY}}"
  -d @classifier.json

### Get a classifier
# @name getClassifier
curl -i -X GET {{AZURE_AI_SERVICE_ENDPOINT}}/contentunderstanding/classifiers/{{CLASSIFIER_ID}}?api-version=2025-05-01-preview
  -H "Ocp-Apim-Subscription-Key: {{AZURE_AI_SERVICE_KEY}}"


### Delete Classifier
# @name deleteClassifier
curl -i -X DELETE "{{AZURE_AI_SERVICE_ENDPOINT}}/contentunderstanding/classifiers/{{CLASSIFIER_ID}}?api-version=2025-05-01-preview"
  -H "Ocp-Apim-Subscription-Key: {{AZURE_AI_SERVICE_KEY}}"


### Submit analysis request
# @name postClassifier
curl -i -X POST "{{AZURE_AI_SERVICE_ENDPOINT}}/contentunderstanding/classifiers/{{CLASSIFIER_ID}}:classify?api-version=2025-05-01-preview"
  -H "Ocp-Apim-Subscription-Key: {{AZURE_AI_SERVICE_KEY}}" \
  -H "Content-Type: application/octet-stream" \
  -d @Lease1.pdf

@classifier_operation_location = {{postClassifier.response.headers.Operation-Location}}


### Get operation status/result dynamically
# @name getClassifierOperationStatus
curl -i -X GET "{{classifier_operation_location}}" \
  -H "Ocp-Apim-Subscription-Key: {{AZURE_AI_SERVICE_KEY}}"
```

### Sample CU classifier result

```json
{
  "id": "3b31320d-8bab-4f88-b19c-2322a7f11034",
  "status": "Succeeded",
  "result": {
    "classifierId": "myClassifier",
    "apiVersion": "2025-05-01-preview",
    "createdAt": "2025-05-01T18:46:36.244Z",
    "contents": [
      {
        "kind": "document",
        "startPageNumber": 1,
        "endPageNumber": 3,
        "category": "invoice",
        "markdown": "# CONTOSO\n\n...",
        "pages": [
          {
            "pageNumber": 1,
            "width": 8.5,
            "height": 11
          },
          {
            "pageNumber": 2,
            "width": 8.5,
            "height": 11
          }
        ],
        "fields": {
          "Company": {
            "type": "string",
            "valueString": "CONTOSO",
            "spans": [
              {
                "offset": 7,
                "length": 2
              }
            ],
            "confidence": 0.95,
            "source": "D(1,5,1,7,1,7,1.5,5,1.5)"
          }
        }
      },
      {
        "kind": "document",
        "startPageNumber": 4,
        "endPageNumber": 4,
        "category": "receipt"
      },
      {
        "kind": "document",
        "startPageNumber": 5,
        "endPageNumber": 5,
        "category": "$OTHER"
      }
    ]
  }
}
```

### Sample CU classifier schema

The CU classifier would be created in Azure AI Foundry, following a schema format similar to the one below:

```json
{
  "description": "test-classifier",
  "tags": {
    "createdBy": "test.user1@microsoft.com"
  },
  "splitMode": "auto",
  "categories": {
    "abstract" : {
      "description": "Abstracts or cover sheet of legal documents"
    },
    "lease_agreement": {
      "description": "Any agreement for any lease agreement",
      "analyzerId": "test-analyzer-v1.0"
    }
  }
}
```

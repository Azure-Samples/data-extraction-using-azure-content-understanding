# Classifier Management API Test Script

This script demonstrates how to use the new classifier management endpoints.

## Endpoints Available

### 1. Create a Classifier
**PUT** `/classifiers/{classifier_id}`

Creates a new classifier with the provided JSON schema.

**Example:**
```bash
curl -X PUT "https://your-function-app.azurewebsites.net/api/classifiers/my-test-classifier" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d @classifier.json
```

**Response:**
```json
{
  "message": "Classifier 'my-test-classifier' created successfully",
  "classifier_id": "my-test-classifier",
  "status": "created"
}
```

### 2. Get a Classifier
**GET** `/classifiers/{classifier_id}`

Retrieves the details of a specific classifier.

**Example:**
```bash
curl -X GET "https://your-function-app.azurewebsites.net/api/classifiers/my-test-classifier" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "classifierId": "my-test-classifier",
  "description": "test-classifier",
  "tags": {
    "createdBy": "test.user1@t-mobile.com"
  },
  "splitMode": "auto",
  "categories": {
    // ... classifier configuration
  }
}
```

## Required JSON Schema Format

When creating a classifier, provide a JSON schema like the one in `src/samples/content-understanding-rest-api/classifier.json`:

```json
{
  "description": "Your classifier description",
  "tags": {
    "createdBy": "your.email@t-mobile.com"
  },
  "splitMode": "auto",
  "categories": {
    "category1": {
      "description": "Description of category 1",
      "analyzerId": "optional-analyzer-id"
    },
    "category2": {
      "description": "Description of category 2"
    }
  }
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:
- **200**: Success (GET operations)
- **201**: Created (PUT operations)
- **400**: Bad Request (missing schema)
- **404**: Not Found (classifier doesn't exist)
- **500**: Internal Server Error

## Authentication

All endpoints require proper authentication using the same role-based access control as the existing configuration endpoints.

## Notes

- Classifier IDs must be unique within the Azure Content Understanding service
- Once created, classifiers can be used in the ingestion pipeline by configuring them in the LeaseAgreementCollectionRow
- The delete functionality is intentionally not exposed through the API for safety reasons
- All operations are logged for audit purposes

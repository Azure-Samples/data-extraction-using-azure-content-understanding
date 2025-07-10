# Deployment Scripts

This directory contains scripts used for data migration between environments. These scripts are designed for specific use cases during environment migration and should be used with caution.

> ⚠️ **WARNING**: These scripts are intended to be run ONLY when migrating data between environments. Running them in normal operation may cause data loss or corruption.

## Available Scripts

### `validate_files.py`

Validates that files referenced in Cosmos DB exist in Azure Storage.

**Usage:**
```powershell
python -m deploy.scripts.validate_files [options]
```

**Options:**
- `--cosmosdb-endpoint`: Cosmos DB endpoint or MongoDB connection string (default: MONGO_CONN_STRING env var)
- `--db-name`: Database name (default: COSMOSDB_DATABASE_NAME env var or "QTMGENAI")
- `--collection-name`: Collection name (default: COLLECTION_NAME env var or "Lease_Documents")
- `--query`: MongoDB query in JSON format to filter documents (default: "{}")
- `--prefix`: Prefix for files in storage (default: "Sites/")
- `--max-documents`: Maximum number of documents to process from Cosmos DB
- `--verbose`: Show verbose output

**Example:**
```powershell
python -m deploy.scripts.validate_files --query "{\"lease_config_hash\": \"c413c56073fc2b8c196a952a0a5e3247a247de8ce1370ae3ca6fdf2b8c2eb163\"}" --prefix "MLA"
```

### `transfer_mongo_data.py`

Transfers data from one MongoDB collection to another using bulk operations.

**Usage:**
```powershell
python -m deploy.scripts.transfer_mongo_data [options]
```

**Options:**
- `--batch-size`: Number of documents to process in each batch (default: 100)
- `--query`: JSON query to filter documents to transfer (default: "{}")
- `--dry-run`: Count documents but don't transfer them
- `--max-docs`: Maximum number of documents to transfer (useful for testing)

**Example:**
```powershell
python -m deploy.scripts.transfer_mongo_data --batch-size 200 --query "{\"site_id\": \"ABC123\"}" --dry-run
```

**Required Environment Variables:**
- `MONGO_CONN_STRING`: MongoDB connection string
- `FROM_DATABASE_NAME`: Source database name
- `TO_DATABASE_NAME`: Target database name
- `FROM_COLLECTION_NAME`: Source collection name
- `TO_COLLECTION_NAME`: Target collection name

### `transfer_storage_data.py`

Transfers data from one Azure Storage account to another.

**Usage:**
```powershell
python -m deploy.scripts.transfer_storage_data [options]
```

## Setup for Running Scripts

1. Make sure you have the required environment variables set in a `.env` file or in your environment:
   ```
   MONGO_CONN_STRING=your_mongodb_connection_string
   COSMOSDB_DATABASE_NAME=your_database_name
   COLLECTION_NAME=your_collection_name
   FROM_DATABASE_NAME=source_db
   TO_DATABASE_NAME=target_db
   FROM_COLLECTION_NAME=source_collection
   TO_COLLECTION_NAME=target_collection
   SA_ACCOUNT_URL=your_storage_account_url
   SA_CONTAINER_NAME=your_container_name
   ```

2. Ensure you have the necessary permissions for both the source and target environments.

3. It's recommended to run a `--dry-run` first to check what would be migrated before performing the actual migration.

4. Consider backing up your data before running migration scripts.

## Best Practices

1. **Always test in a non-production environment first**: Before running any migration script in production, ensure it works as expected in a test environment.

2. **Use query filters**: Limit the scope of data migration using appropriate query filters to reduce risk.

3. **Monitor execution**: Watch the script execution and check logs for any errors or warnings.

4. **Validate after migration**: Use the validation scripts to ensure data was migrated correctly.

5. **Document all migrations**: Keep track of when and why migrations were performed for future reference.

## Troubleshooting

- If a script fails, check the log files generated in the root directory of the project.
- For connection issues, verify that your environment variables are set correctly.
- For permission issues, ensure that the credentials used have appropriate access to both source and target resources.

## Security Considerations

These scripts handle sensitive data and should be run with appropriate security precautions:

1. Never commit sensitive credentials or connection strings to version control.
2. Use environment variables or secure credential stores for sensitive information.
3. Run scripts with the minimum required permissions.

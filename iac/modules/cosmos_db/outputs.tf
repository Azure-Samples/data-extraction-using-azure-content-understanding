output "output" {
  description = <<DESCRIPTION
The output of the Cosmos DB AVM module.
See: https://registry.terraform.io/modules/Azure/avm-res-documentdb-databaseaccount/azurerm/0.6.0
DESCRIPTION
  value       = module.cosmosdb
}

output "resource_id" {
  description = "CosmosDB resource id"
  value       = module.cosmosdb.resource_id
}

output "name" {
  description = "CosmosDB name"
  value       = module.cosmosdb.name
}

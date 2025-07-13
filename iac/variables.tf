variable "resource_group_location" {
  type        = string
  description = "Location of the resource group."
}

variable "resource_group_location_abbr" {
  type        = string
  description = "Abbreviation for Location of the resource group."
}

variable "environment_name" {
  type        = string
  description = "The name of environment."
}

variable "usecase_name" {
  type        = string
  description = "The name of the usecase."
}

variable "subscription_id" {
  type        = string
  description = "The subscription ID to use for the resources."
}

variable "foundry_managed_network" {
  type = object({
    isolation_mode = string
    spark_ready    = optional(bool, true)
  })
  default = {
    isolation_mode = "Disabled"
    spark_ready    = true
  }
  description = <<DESCRIPTION
Specifies properties of foundry's managed virtual network.

Possible values for `isolation_mode` are:
- 'Disabled': Inbound and outbound traffic is unrestricted _or_ BYO VNet to protect resources.
- 'AllowInternetOutbound': Allow all internet outbound traffic.
- 'AllowOnlyApprovedOutbound': Outbound traffic is allowed by specifying service tags.
While is possible to update foundry to enable network isolation ('AllowInternetOutbound' or 'AllowOnlyApprovedOutbound'), it is not possible to disable it on foundry with it enabled.

`spark_ready` determines whether spark jobs will be run on the network. This value can be updated in the future.
DESCRIPTION
}

variable "deploy_ai_search" {
  type        = bool
  default     = false
  description = "Deploy Azure Cognitive Search."
}

variable "deploy_app_insights_for_foundry" {
  type        = bool
  default     = true
  description = "Deploy Application Insights for Foundry."
}

variable "ai_app_insights_local_authentication_disabled" {
  type        = bool
  default     = true
  description = "Disable local authentication for Application Insights."
}

variable "ai_app_insights_internet_ingestion_enabled" {
  type        = bool
  default     = false
  description = "Enable internet ingestion for Application Insights."
}

variable "ai_app_insights_internet_query_enabled" {
  type        = bool
  default     = false
  description = "Enable internet query for Application Insights."
}

variable "infrastructure_encryption_enabled" {
  type        = bool
  default     = false
  description = "Enable infrastructure encryption."
}

variable "cognitive_deployments" {
  type = map(object({
    name = string
    model = object({
      format  = string
      name    = string
      version = string
    })
    scale = object({
      type = string
    })
    rai_policy_name = string
  }))
  default = {
    "gpt-4o" = {
      name = "gpt-4o"
      model = {
        format  = "OpenAI"
        name    = "gpt-4o"
        version = "2024-08-06"
      }
      scale = {
        type = "Standard"
      }
      rai_policy_name = "Microsoft.DefaultV2"
    }
  }
  description = <<DESCRIPTION
  A map of cognitive model deployments to create on the Azure OpenAI Cognitive Services account. The map key is deliberately arbitrary to avoid issues where map keys maybe unknown at plan time.
  - `name` - (Required) The name of the deployment.
  - `model` - (Required) The model to deploy.
    - `format` - "OpenAI"
    - `name` - The name of the model to deploy.
    - `version` - The version of the model to deploy.
  - `scale` - (Required) The scale of the model.
    - `type` - The type of scale to use. Possible values are `Standard`.
  - `rai_policy_name` - (Required) The name of the RAI policy to use for the deployment.
  example:
  ```
  {
    "gpt-4" = {
      name = "gpt-4"
      model = {
        format  = "OpenAI"
        name    = "gpt-4"
        version = "0125-Preview"
      }
      scale = {
        type = "Standard"
      }
      rai_policy_name = "Microsoft.DefaultV2"
    }
    "text-embedding-ada-002" = {
      name = "text-embedding-ada-002"
      model = {
        format  = "OpenAI"
        name    = "text-embedding-ada-002"
        version = "2"
      }
      scale = {
        type = "Standard"
      }
      rai_policy_name = "Microsoft.DefaultV2"
    }
  }
  ```
  DESCRIPTION
}

variable "ai_projects" {
  type = map(object({
    name          = string
    description   = string
    friendly_name = string
  }))
  default = {
    "foundry_rag_project" = {
      name          = "rag-project"
      description   = "This is secure AI RAG project using foundry."
      friendly_name = "AI Foundry RAG Project"
    }
  }
  description = <<DESCRIPTION
  A map of AI projects to create in the Azure Foundry.
  - `name` - (Required) The name of the project.
  - `description` - (Required) The description of the project.
  - `friendly_name` - (Required) The friendly name of the project.
  example:
```
  {

    "project" = {
      name        = "<project1_name>"
      description = "This is secure AI project"
      friendly_name = "AI Project"
    }
  }
  ```
DESCRIPTION
}

variable "deploy_ai_services" {
  type        = bool
  default     = true
  description = "Deploy Azure AI Services."
}

variable "enable_telemetry" {
  description = "Flag to enable telemetry for modules"
  type        = bool
  default     = false
}


variable "use_customer_managed_key_encryption" {
  type        = bool
  default     = false
  description = "Whether or not to use customer managed key encryption"
}


variable "cosmosdb_mongo_databases" {
  type = map(object({
    name       = string
    throughput = number
    collections = map(object({
      name       = string
      shard_key  = string
      throughput = number
      index = object({
        keys   = list(string)
        unique = bool
      })
    }))
  }))
  description = <<DESCRIPTION
A map of Cosmos DB MongoDB API databases to create. The map key is deliberately arbitrary to avoid issues where map keys may be unknown at plan time.
- `name` - (Required) The name of the database.
- `throughput` - (Required) The throughput for the database in RU/s.
- `collections` - (Required) A map of collections to create within the database. Each collection must have:
  - `name` - (Required) The name of the collection.
  - `shard_key` - (Required) The shard key for the collection.
  - `throughput` - (Required) The throughput for the collection in RU/s.
  - `index` - (Required) An object defining the index for the collection, which includes:
    - `keys` - (Required) A list of keys for the index.
    - `unique` - (Required) A boolean indicating whether the index is unique.
DESCRIPTION
  default = {
    "default_database" = {
      name       = "data-extraction-db"
      throughput = 400
      collections = {
        "Configurations" = {
          name       = "Configurations"
          shard_key  = "_id"
          throughput = 400
          index = {
            keys   = ["_id"]
            unique = true
          }
        },
        "Documents" = {
          name       = "Documents"
          shard_key  = "_id"
          throughput = 400
          index = {
            keys   = ["_id"]
            unique = true
          }
        }
      }
    }
  }
}


variable "location" {
  description = "The Azure region where resources will be created. Content Understanding is only available in: West US (westus), Sweden Central (swedencentral), Australia East (australiaeast)"
  type        = string
  default     = "West US"
  validation {
    condition = contains([
      "West US",
      "Sweden Central", 
      "Australia East",
      "westus",
      "swedencentral",
      "australiaeast"
    ], var.location)
    error_message = "Content Understanding is only available in: West US (westus), Sweden Central (swedencentral), Australia East (australiaeast)."
  }
}

variable "subscription_id" {
  description = "The Azure subscription ID where resources will be deployed"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "A map of tags to assign to resources"
  type        = map(string)
  default = {
    Environment = "dev"
    Project     = "data-extraction"
    Owner       = "development-team"
  }
}

variable "cosmos_consistency_level" {
  description = "The consistency level for CosmosDB"
  type        = string
  default     = "Session"
  validation {
    condition = contains([
      "BoundedStaleness",
      "Eventual",
      "Session",
      "Strong",
      "ConsistentPrefix"
    ], var.cosmos_consistency_level)
    error_message = "Cosmos consistency level must be one of: BoundedStaleness, Eventual, Session, Strong, ConsistentPrefix."
  }
}

variable "storage_account_tier" {
  description = "The tier for the storage account"
  type        = string
  default     = "Standard"
  validation {
    condition = contains([
      "Standard",
      "Premium"
    ], var.storage_account_tier)
    error_message = "Storage account tier must be either Standard or Premium."
  }
}

variable "storage_replication_type" {
  description = "The replication type for the storage account"
  type        = string
  default     = "LRS"
  validation {
    condition = contains([
      "LRS",
      "GRS",
      "RAGRS",
      "ZRS",
      "GZRS",
      "RAGZRS"
    ], var.storage_replication_type)
    error_message = "Storage replication type must be one of: LRS, GRS, RAGRS, ZRS, GZRS, RAGZRS."
  }
}

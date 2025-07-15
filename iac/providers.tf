terraform {
  required_version = ">= 1.9"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0.0, < 5.0.0"
    }
    # https://registry.terraform.io/providers/hashicorp/random/latest
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0.0, < 4.0.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.3"
    }
    azapi = {
      source  = "Azure/azapi"
      version = ">= 1.14.0, < 3.0.0"
    }
  }
}

provider "azurerm" {
  storage_use_azuread = true
  features {
    key_vault {
      recover_soft_deleted_key_vaults    = false
      purge_soft_delete_on_destroy       = false
      purge_soft_deleted_keys_on_destroy = false
    }
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }

  subscription_id = var.subscription_id
}

provider "azuread" {
  partner_id = var.enable_telemetry ? "acce1e78-24be-4ea5-93c6-0f400bc653e1" : null
}

provider "azapi" {
  partner_id = var.enable_telemetry ? "acce1e78-24be-4ea5-93c6-0f400bc653e1" : null
}

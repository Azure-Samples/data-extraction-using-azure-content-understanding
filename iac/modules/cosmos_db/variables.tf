variable "location" {
  type        = string
  description = "The location/region where the resources will be deployed."
  nullable    = false
}

variable "name" {
  type        = string
  description = "The name of the this resource."

  validation {
    condition     = can(regex("^[a-zA-Z0-9]+(-[a-zA-Z0-9]+)*$", var.name))
    error_message = "The name can only include alphanumeric characters and hyphens, and can't start or end with a hyphen."
  }
}

# This is required for most resource modules
variable "resource_group_name" {
  type        = string
  description = "The resource group where the resources will be deployed."
}

variable "enable_telemetry" {
  type        = bool
  default     = true
  description = <<DESCRIPTION
This variable controls whether or not telemetry is enabled for the module.
For more information see <https://aka.ms/avm/telemetryinfo>.
If it is set to false, then no telemetry will be collected.
As explained in the [AVM documentation](https://azure.github.io/Azure-Verified-Modules/help-support/telemetry/),
Microsoft relies on telemetry to identify the deployments of the AVM Modules.
Deployments are identified through a specific GUID (Globally Unique ID), indicating that the code originated from AVM.
The data is collected and governed by Microsoft’s privacy policies, found in the [Trust Center](https://www.microsoft.com/trust-center).
Telemetry collected does not provide Microsoft with insights into the resources deployed,
their configuration or any customer data stored in or processed by Azure resources deployed by using code from AVM.
Microsoft does not track the usage/consumption of individual resources using telemetry.
Telemetry collection is strictly optional, and it can easily be opted out of by following
[these procedures](https://azure.github.io/Azure-Verified-Modules/help-support/telemetry/#opting-out).
DESCRIPTION
}

variable "role_assignments" {
  description = "Optional role assignments for private endpoints"
  type = map(object({
    role_definition_id_or_name = string
    description                = string
    principal_id               = string
  }))
  default = {}
}

variable "sql_databases" {
  description = "Optional SQL databases and containers configuration"
  type = map(object({
    name = string
    containers = map(object({
      name                = string
      partition_key_paths = list(string)
      throughput          = optional(number, null)
    }))
  }))
  default = {}
}

variable "managed_identities" {
  description = "Optional Managed Identity configuration for the resource"
  type = object({
    type       = optional(string, "SystemAssigned")
    identities = optional(set(string), [])
  })
  default = {
    type = "SystemAssigned"
  }
}

variable "tags" {
  type        = map(string)
  default     = null
  description = "A map of tags to add to all resources"
}

variable "diagnostic_settings" {
  type = map(object({
    name                  = optional(string, null)
    workspace_resource_id = optional(string, null)
  }))
  default     = {}
  description = "Diagnostic settings for the resource"
}

variable "analytical_storage_enabled" {
  type        = bool
  default     = true
  description = "Enable analytical storage for the CosmosDB account."
}

variable "public_network_access_enabled" {
  type        = bool
  default     = true
  description = "Whether or not public network access is allowed for this server."
}

variable "private_endpoints_manage_dns_zone_group" {
  type        = bool
  default     = false
  description = "Whether the module should manage the private DNS zone group for private endpoints."
}

variable "mongo_server_version" {
  type        = string
  default     = null
  description = "The Server Version of a MongoDB account. Possible values are 4.2, 4.0, 3.6, and 3.2."
}

variable "geo_locations" {
  type = list(object({
    location          = string
    failover_priority = number
    zone_redundant    = optional(bool, false)
  }))
  description = "The geo-replication locations for the CosmosDB account."
}

variable "capabilities" {
  type = list(object({
    name = string
  }))
  default     = []
  description = "List of capabilities to enable for the CosmosDB account."
}

variable "mongo_databases" {
  type        = map(any)
  default     = {}
  description = "Map of MongoDB databases to create."
}


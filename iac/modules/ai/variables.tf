variable "location" {
  type        = string
  description = "The location/region where the resources will be deployed."
  nullable    = false
}

variable "name" {
  type        = string
  description = "The name of the this resource."

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{4,14}$", var.name))
    error_message = "The name must be between 5 and 15 chars long and can only contain lowercase letters and numbers."
  }
}

# This is required for most resource modules
variable "resource_group_name" {
  type        = string
  description = "The resource group where the resources will be deployed."
}

variable "customer_managed_key" {
  type = object({
    key_vault_resource_id = optional(string, null)
    key_name              = optional(string, null)
    key_version           = optional(string, null)
    user_assigned_identity = optional(object({
      resource_id = string
    }), null)
  })
  default     = null
  description = <<DESCRIPTION
A map describing customer-managed keys to associate with the resource. This includes the following properties:
- `key_vault_resource_id` - The resource ID of the Key Vault where the key is stored.
- `key_name` - The name of the key.
- `key_version` - (Optional) The version of the key. If not specified, the latest version is used.
- `user_assigned_identity` - (Optional) An object representing a user-assigned identity with the following properties:
  - `resource_id` - The resource ID of the user-assigned identity.
DESCRIPTION
}

variable "dod_il4" {
  type        = bool
  default     = false
  description = "Enable US DoD Impact Level 4 compliance settings."
}

variable "dod_il5" {
  type        = bool
  default     = false
  description = "Enable US DoD Impact Level 5 compliance settings."
}

variable "key_vault_resource_id" {
  type        = string
  description = "The resource_id of the Azure Key Vault."
}

variable "infrastructure_encryption_enabled" {
  type        = bool
  default     = false
  description = "Enable infrastructure encryption."
}

variable "dns_zones" {
  description = "List of private DNS zone names to create"
  type        = list(string)
  default = [
    "privatelink.cognitiveservices.azure.com",
    "privatelink.openai.azure.com",
    "privatelink.search.windows.net",
    "privatelink.api.azureml.ms",
    "privatelink.notebooks.azure.net",
    #    "privatelink.blob.core.windows.net",
    "privatelink.file.core.windows.net",
    "privatelink.table.core.windows.net",
    "privatelink.queue.core.windows.net",
    "privatelink.services.ai.azure.com"
  ]
}

variable "blob_storage_account_dns_zone" {
  type = object({
    id   = string
    name = string
  })
  description = "The name and resource id of the DNS zone created for privatelink.blob.core.windows.net"
  default     = null
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

variable "key_vault_name" {
  type        = string
  default     = ""
  description = "The name of the Azure Key Vault. If not provided, a name will be generated."
}

variable "kind" {
  type        = string
  default     = "Default"
  description = <<DESCRIPTION
The kind of the resource. This is used to determine the type of the resource. If not specified, the resource will be created as a standard resource.
Possible values are:
- `Default` - The resource will be created as a standard Azure Machine Learning resource.
- `hub` - The resource will be created as an Azure AI Hub resource.
DESCRIPTION
}

variable "lock" {
  type = object({
    kind = string
    name = optional(string, null)
  })
  default     = null
  description = <<DESCRIPTION
Controls the Resource Lock configuration for this resource. The following properties can be specified:

- `kind` - (Required) The type of lock. Possible values are `\"CanNotDelete\"` and `\"ReadOnly\"`.
- `name` - (Optional) The name of the lock. If not specified, a name will be generated based on the `kind` value. Changing this forces the creation of a new resource.
DESCRIPTION

  validation {
    condition     = var.lock != null ? contains(["CanNotDelete", "ReadOnly"], var.lock.kind) : true
    error_message = "The lock level must be one of: 'None', 'CanNotDelete', or 'ReadOnly'."
  }
}

variable "machine_learning_workspace_name" {
  type        = string
  default     = ""
  description = "The name of the Azure Machine Learning Workspace. If not provided, a name will be generated."
}

variable "create_compute_instance" {
  type        = bool
  default     = false
  description = "Specifies whether a compute instance should be created for the workspace to provision the managed vnet."
}

variable "workspace_managed_network" {
  type = object({
    isolation_mode = string
    spark_ready    = optional(bool, true)
  })
  default = {
    isolation_mode = "Disabled"
    spark_ready    = true
  }
  description = <<DESCRIPTION
Specifies properties of the workspace's managed virtual network.

Possible values for `isolation_mode` are:
- 'Disabled': Inbound and outbound traffic is unrestricted _or_ BYO VNet to protect resources.
- 'AllowInternetOutbound': Allow all internet outbound traffic.
- 'AllowOnlyApprovedOutbound': Outbound traffic is allowed by specifying service tags.
While is possible to update the workspace to enable network isolation ('AllowInternetOutbound' or 'AllowOnlyApprovedOutbound'), it is not possible to disable it on a workspace with it enabled.

`spark_ready` determines whether spark jobs will be run on the network. This value can be updated in the future.
DESCRIPTION
}

variable "role_assignments" {
  type = map(object({
    role_definition_name                   = string
    role_definition_id                     = string
    principal_id                           = string
    description                            = optional(string, null)
    skip_service_principal_aad_check       = optional(bool, false)
    condition                              = optional(string, null)
    condition_version                      = optional(string, null)
    delegated_managed_identity_resource_id = optional(string, null)
    principal_type                         = optional(string, null)
  }))
  default     = {}
  description = <<DESCRIPTION
  A map of role assignments to create on the `RESOURCE`. The map key is deliberately arbitrary to avoid issues where map keys maybe unknown at plan time.

  - `role_definition_id_or_name` - The ID or name of the role definition to assign to the principal.
  - `principal_id` - The ID of the principal to assign the role to.
  - `description` - (Optional) The description of the role assignment.
  - `skip_service_principal_aad_check` - (Optional) If set to true, skips the Azure Active Directory check for the service principal in the tenant. Defaults to false.
  - `condition` - (Optional) The condition which will be used to scope the role assignment.
  - `condition_version` - (Optional) The version of the condition syntax. Leave as `null` if you are not using a condition, if you are then valid values are '2.0'.
  - `delegated_managed_identity_resource_id` - (Optional) The delegated Azure Resource Id which contains a Managed Identity. Changing this forces a new resource to be created. This field is only used in cross-tenant scenario.
  - `principal_type` - (Optional) The type of the `principal_id`. Possible values are `User`, `Group` and `ServicePrincipal`. It is necessary to explicitly set this attribute when creating role assignments if the principal creating the assignment is constrained by ABAC rules that filters on the PrincipalType attribute.

  > Note: only set `skip_service_principal_aad_check` to true if you are assigning a role to a service principal.
  DESCRIPTION
  nullable    = false
}

variable "tags" {
  type        = map(string)
  default     = null
  description = "A map of tags to add to all resources"
}

variable "virtual_network_name" {
  type        = string
  default     = ""
  description = "The name of the Virtual Network. If not provided, a name will be generated."
}

variable "container_registry_name" {
  type        = string
  default     = ""
  description = "The name of the Azure Container Registry. If not provided, a name will be generated."
}

variable "vnet_id" {
  type        = string
  default     = ""
  description = "The id of the vnet."
}

variable "container_registry_resource_id" {
  type        = string
  default     = ""
  description = "The resource_id of the Azure Container Registry."
}

variable "log_analytics_workspace_resource_id" {
  type        = string
  default     = ""
  description = "The resource_id of the Log Analytics Workspace."
}

variable "aml_storage_account_name" {
  type        = string
  default     = ""
  description = "The dedicated name for the AML Storage Account."
}

variable "diagnostic_settings" {
  type = map(object({
    name                  = optional(string, null)
    workspace_resource_id = optional(string, null)
  }))
}

variable "aiservices_name" {
  type        = string
  default     = ""
  description = "The name of the Azure AI Services. If not provided, a name will be generated."
}

variable "aisearch_allowed_ips" {
  type        = list(string)
  default     = []
  description = "A list of IP addresses that are allowed to access the AI Search service."
}

variable "aisearch_hosting_mode" {
  type        = string
  default     = null
  description = "(Optional) Specifies the Hosting Mode, which allows for High Density partitions (that allow for up to 1000 indexes) should be supported. Possible values are `highDensity` or `default`. Defaults to `default`. Changing this forces a new Search Service to be created."
}

variable "aisearch_partition_count" {
  type        = number
  default     = 1
  description = "Number of Partitions."

  validation {
    condition     = contains([1, 2, 3, 4, 6, 12], var.aisearch_partition_count)
    error_message = "The partition_count must be one of the following values: 1, 2, 3, 4, 6, 12."
  }
}

variable "aisearch_replica_count" {
  type        = number
  default     = 1
  description = "Number of Replicas."

  validation {
    condition     = var.aisearch_replica_count >= 1 && var.aisearch_replica_count <= 12
    error_message = "The replica_count must be between 1 and 12."
  }
}

variable "aisearch_semantic_search_sku" {
  type        = string
  default     = "free"
  description = "(Optional) Specifies the Semantic Search SKU which should be used for this AI Search Service. Possible values include `free` and `standard`."
}

variable "aisearch_sku" {
  type        = string
  default     = "basic"
  description = "The SKU of the AI Search service."
}

variable "azureopenai_name" {
  type        = string
  default     = ""
  description = "The name of the Azure OpenAI Cognitive Services account. If not provided, a name will be generated."
}

variable "azureopenai_sku" {
  type        = string
  default     = "S0"
  description = "The SKU of the Azure OpenAI Cognitive Services account."
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
  default     = {}
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

variable "deploy_ai_search" {
  type        = bool
  default     = false
  description = "Conditional variable for deploying AI Search"
}

variable "deploy_aoai" {
  type        = bool
  default     = false
  description = "Conditional variable for deploying Azure OpenAI"
}

variable "deploy_ai_services" {
  type        = bool
  default     = false
  description = "Conditional variable for deploying Azure AI Services"
}

variable "deploy_app_insights_for_aml" {
  type        = bool
  default     = false
  description = <<DESCRIPTION
  "If set to true, an new Application Insights service will be provisioned for usage with AML"
  "If set to false, an existing Application Insights instance will been to be passed to AML"
DESCRIPTION
}

variable "deploy_ai_projects" {
  type        = bool
  default     = true
  description = "Conditional variable for deploying Azure AI projects."
}

variable "ai_projects" {
  type = map(object({
    name          = string
    description   = string
    friendly_name = string
  }))
  default     = {}
  description = "List of AI projects that will be deployed in the AI hub. Each project should have a name, description and a friendly name."
  validation {
    condition = var.kind == "Hub" ? length(var.ai_projects) > 0 : true
    # The condition checks if the kind is 'hub' and if so, it ensures that at least one AI project is specified.
    # If the kind is not 'hub', it allows for an empty list of AI projects.
    # If the kind is 'hub', then at least one AI project must be specified.
    error_message = "If the kind is set to 'hub', then at least one AI project must be specified."
  }
}

variable "ai_app_insights_azure_monitor_private_link_scoped_service_name" {
  type        = string
  default     = ""
  description = "If deploying a new App Insights instance for AML, the name of the AMPLS Scoped Service for App Insights. If not provided, a name will be generated."
}

variable "ai_app_insights_name" {
  type        = string
  default     = ""
  description = "The name of the Application Insights instance. If not provided, a name will be generated."
}

variable "existing_dsusers_group" {
  description = "Existing ds users group name and id for role based access control"
  type = object({
    name = string
    id   = string
  })
  default = null
}

variable "ds_group_members" {
  type        = list(string)
  default     = []
  description = "List of user object ids to enable role based access to the AI resources"
}

variable "ds_access_roles" {
  type        = list(string)
  default     = []
  description = "List of roles to assign to the Data Science group"
}

variable "azure_ai_docintel_local_authentication_enabled" {
  type        = bool
  default     = true
  description = "Controls whether or not local authentication is enabled for the Azure Document Intelligence Service."
}

variable "azure_ai_docintel_sku" {
  type        = string
  default     = "F0"
  description = "The SKU of the Azure Document Intelligence Service."
}

variable "azure_ai_contentsafety_name" {
  type        = string
  default     = ""
  description = "The name of the Azure AI Content Safety Service. If not provided, a name will be generated."
}

variable "azure_ai_contentsafety_sku" {
  type        = string
  default     = "S0"
  description = "The SKU of the Azure AI Content Safety Service."
}

variable "ai_app_insights_local_authentication_disabled" {
  type        = bool
  default     = false
  description = "(Optional) Disable Non-Azure AD based Auth"
}

variable "ai_app_insights_internet_ingestion_enabled" {
  type        = bool
  default     = true
  description = "(Optional) Should the Application Insights component support ingestion over the Public Internet?"
}

variable "ai_app_insights_internet_query_enabled" {
  type        = bool
  default     = true
  description = "(Optional) Should the Application Insights component support querying over the Public Internet?"
}

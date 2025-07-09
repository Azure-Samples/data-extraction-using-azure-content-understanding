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



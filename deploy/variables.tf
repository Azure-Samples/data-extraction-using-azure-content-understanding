variable "location" {
  description = "The Azure region where resources will be created."
  type        = string
  default     = "West US"
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



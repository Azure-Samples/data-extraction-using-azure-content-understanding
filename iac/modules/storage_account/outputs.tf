# Module owners should include the resource id via a 'resource_id' output
# https://azure.github.io/Azure-Verified-Modules/specs/terraform/#id-tffr2---category-outputs---additional-terraform-outputs
output "output" {
  description = "The storage_account module"
  value       = module.storage_account
}

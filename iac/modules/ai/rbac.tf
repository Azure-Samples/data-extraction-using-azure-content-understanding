# Create the Azure AD group

resource "azuread_group" "caira_ds_group" {
  count            = var.existing_dsusers_group == null && length(var.ds_group_members) > 0 ? 1 : 0
  display_name     = "CAIRA-DataScientist-Group-${var.name}"
  description      = "Group for CAIRA Data Scientist persona"
  mail_enabled     = false
  security_enabled = true
}

# Create the role assignments
locals {
  ds_access_roles = toset(var.ds_access_roles)
}

# TBD : scope restriction for fine grained access control
resource "azurerm_role_assignment" "ds_access_role_assignments" {
  for_each             = local.ds_access_roles
  principal_id         = var.existing_dsusers_group != null ? var.existing_dsusers_group.id : azuread_group.caira_ds_group[0].object_id
  scope                = data.azurerm_resource_group.ai.id
  role_definition_name = each.key
  lifecycle {
    ignore_changes = [
      # Ignore changes to these attributes to prevent force-replacement
      scope,
      role_definition_id,
      principal_type
    ]
  }
}

# associate user object ids to the groups for the role assignments

locals {
  ds_group_members = toset(var.ds_group_members)
}

resource "azuread_group_member" "caira_ds_group_member" {
  for_each = local.ds_group_members

  group_object_id  = var.existing_dsusers_group != null ? var.existing_dsusers_group.id : azuread_group.caira_ds_group[0].object_id
  member_object_id = each.key
}

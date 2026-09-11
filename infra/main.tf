# Foundry (AIServices) account, its project, model deployments, and the
# developer role assignment.

locals {
  # Resource group name. Falls back to rg-{environment_name} when not provided.
  resource_group_name = (
    var.resource_group_name != "" ? var.resource_group_name : "rg-${local.derived_rg_suffix}"
  )
  derived_rg_suffix = trimsuffix(
    substr(trim(coalesce(var.environment_name, "env"), "-."), 0, 87),
    "-",
  )

  # Token to keep globally-unique resource names stable across re-provisions.
  resource_token = substr(sha1(join("-", compact([
    var.subscription_id,
    local.resource_group_name,
    var.location,
    var.resource_token_salt,
  ]))), 0, 13)

  # Use a deterministic fresh name; the previous name was restored from a
  # soft-deleted account whose policy state rejected model deployment.
  foundry_account_name = "cog-${local.resource_token}-fresh2"

  # Project name. Falls back to a sanitized environment_name (3-32 chars) when
  # not provided.
  foundry_project_name = (
    var.foundry_project_name != "" ? var.foundry_project_name : local.derived_project_name
  )

  sanitized_env_name = trim(
    replace(lower(coalesce(var.environment_name, "")), "/[^a-z0-9-]/", "-"),
    "-",
  )
  # substr errors when length exceeds the string, so only truncate when needed.
  capped_env_name = (
    length(local.sanitized_env_name) > 32
    ? substr(local.sanitized_env_name, 0, 32)
    : local.sanitized_env_name
  )
  derived_project_name = (
    length(local.capped_env_name) >= 3
    ? local.capped_env_name
    : (local.capped_env_name == "" ? "foundryproject" : "${local.capped_env_name}prj")
  )

  # https://learn.microsoft.com/azure/role-based-access-control/built-in-roles
  cognitive_services_user_role_id = "a97b65f3-24c7-4388-baec-2e87135dc908"
}

resource "azurerm_resource_group" "this" {
  name     = local.resource_group_name
  location = var.location
  tags     = var.tags
}

# azapi is used so allowProjectManagement can be set (not exposed by
# azurerm_cognitive_account).
resource "azapi_resource" "foundry_account" {
  type      = "Microsoft.CognitiveServices/accounts@2025-06-01"
  name      = local.foundry_account_name
  location  = azurerm_resource_group.this.location
  parent_id = azurerm_resource_group.this.id
  tags      = var.tags

  identity {
    type = "SystemAssigned"
  }

  body = {
    kind = "AIServices"
    sku = {
      name = "S0"
    }
    properties = {
      allowProjectManagement = true
      customSubDomainName    = local.foundry_account_name
      publicNetworkAccess    = "Enabled"
      disableLocalAuth       = true
      networkAcls = {
        defaultAction       = "Allow"
        virtualNetworkRules = []
        ipRules             = []
      }
    }
  }
}

# Created one at a time; ARM throttles rapid repeated deployments on one account.
# AzAPI keeps the deployment on the stable 2025-06-01 ARM contract.
resource "azapi_resource" "model" {
  for_each = { for d in var.deployments : d.name => d }

  type      = "Microsoft.CognitiveServices/accounts/deployments@2025-06-01"
  name      = each.value.name
  parent_id = azapi_resource.foundry_account.id

  body = {
    properties = {
      model = {
        format  = each.value.model.format
        name    = each.value.model.name
        version = each.value.model.version
      }
    }
    sku = {
      name     = each.value.sku.name
      capacity = each.value.sku.capacity
    }
  }

}

# Created after all model deployments complete.
resource "azapi_resource" "project" {
  type      = "Microsoft.CognitiveServices/accounts/projects@2025-06-01"
  name      = local.foundry_project_name
  location  = azurerm_resource_group.this.location
  parent_id = azapi_resource.foundry_account.id

  identity {
    type = "SystemAssigned"
  }

  body = {
    properties = {
      description = "${local.foundry_project_name} Project"
      displayName = local.foundry_project_name
    }
  }

  response_export_values = ["identity.principalId"]

  depends_on = [azapi_resource.model]
}

# Grants the developer Cognitive Services User on the project to call the
# Foundry data-plane (chat/completions, agents API). Skipped when principal_id
# is empty.
resource "azurerm_role_assignment" "developer_cognitive_services_user" {
  count = var.principal_id == "" ? 0 : 1

  scope              = azapi_resource.project.id
  role_definition_id = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/${local.cognitive_services_user_role_id}"
  principal_id       = var.principal_id
  principal_type     = var.principal_type
}

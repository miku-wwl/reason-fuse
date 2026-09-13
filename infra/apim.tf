variable "publisher_email" {
  type = string
}

resource "azurerm_api_management" "validation" {
  name                = "apim-rf-${local.resource_token}"
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name
  publisher_name      = "ReasonFuse Phase 6"
  publisher_email     = var.publisher_email
  sku_name            = "Consumption_0"
}

resource "azurerm_api_management_backend" "release" {
  for_each            = toset(["stable", "candidate"])
  name                = each.key
  resource_group_name = azurerm_resource_group.this.name
  api_management_name = azurerm_api_management.validation.name
  protocol            = "http"
  url                 = "https://${azapi_resource.foundry_account.name}.services.ai.azure.com/api/projects/${azapi_resource.project.name}/agents/reasonfuse-phase6-${each.key}/endpoint/protocols/openai"
}

# AzureRM's Single backend resource does not expose the pool/affinity fields.
resource "azapi_resource" "canary_pool" {
  type      = "Microsoft.ApiManagement/service/backends@2025-03-01-preview"
  name      = "reasonfuse-canary"
  parent_id = azurerm_api_management.validation.id
  body = {
    properties = {
      type = "Pool"
      pool = {
        services = [
          { id = azurerm_api_management_backend.release["stable"].id, priority = 1, weight = 95 },
          { id = azurerm_api_management_backend.release["candidate"].id, priority = 1, weight = 5 }
        ]
        sessionAffinity = {
          sessionId = { source = "cookie", name = "ReasonFuseAffinity" }
        }
      }
    }
  }
}

resource "azurerm_api_management_api" "responses" {
  name                = "reasonfuse"
  resource_group_name = azurerm_resource_group.this.name
  api_management_name = azurerm_api_management.validation.name
  revision            = "1"
  display_name        = "ReasonFuse Phase 6"
  path                = "reasonfuse"
  protocols           = ["https"]
  # The original Entra bearer token passes through; Foundry enforces caller RBAC.
  subscription_required = false
}

resource "azurerm_api_management_api_operation" "post" {
  for_each            = toset(["responses", "conversations"])
  operation_id        = "post-${each.key}"
  api_name            = azurerm_api_management_api.responses.name
  api_management_name = azurerm_api_management.validation.name
  resource_group_name = azurerm_resource_group.this.name
  display_name        = "POST ${each.key}"
  method              = "POST"
  url_template        = "/${each.key}"
}

resource "azurerm_api_management_api_policy" "streaming" {
  api_name            = azurerm_api_management_api.responses.name
  api_management_name = azurerm_api_management.validation.name
  resource_group_name = azurerm_resource_group.this.name
  xml_content         = file("${path.module}/apim-policy.xml")
  depends_on          = [azapi_resource.canary_pool]
}

resource "azurerm_api_management_logger" "metadata" {
  name                = "phase6-metadata"
  api_management_name = azurerm_api_management.validation.name
  resource_group_name = azurerm_resource_group.this.name
  application_insights {
    instrumentation_key = azurerm_application_insights.validation.instrumentation_key
  }
}

resource "azurerm_api_management_api_diagnostic" "metadata" {
  identifier                = "applicationinsights"
  api_name                  = azurerm_api_management_api.responses.name
  api_management_name       = azurerm_api_management.validation.name
  resource_group_name       = azurerm_resource_group.this.name
  api_management_logger_id  = azurerm_api_management_logger.metadata.id
  sampling_percentage       = 100
  always_log_errors         = true
  log_client_ip             = false
  verbosity                 = "information"
  http_correlation_protocol = "W3C"
  frontend_request { body_bytes = 0 }
  frontend_response { body_bytes = 0 }
  backend_request { body_bytes = 0 }
  backend_response { body_bytes = 0 }
}

output "APIM_ENDPOINT" {
  value = "${azurerm_api_management.validation.gateway_url}/reasonfuse"
}

output "APIM_NAME" {
  value = azurerm_api_management.validation.name
}

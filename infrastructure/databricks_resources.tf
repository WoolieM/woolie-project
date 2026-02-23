# Example: Creating a Secret Scope for your CoinGecko API Key
resource "databricks_secret_scope" "api_keys" {
  name = "tokens"
}
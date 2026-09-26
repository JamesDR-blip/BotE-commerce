# Writing a Plugin

## Supported package categories

The marketplace domain currently defines:

- `rule_pack`
- `validator_plugin`
- `channel_connector`

## Manifest contracts

A `RulePackManifest` describes package ID, version, publisher, interface version, category and rules path.

The rules path must be relative and must not contain parent-directory traversal.

A `PluginManifest` describes package ID, version, publisher, interface version, entrypoint, artifact path and dependencies.

The artifact path must be relative and must not contain parent-directory traversal.

The entrypoint uses `<module>:<attribute>` format.

## Marketplace package identity

`MarketplacePackage` contains package ID, version, package type, publisher, interface version, content hash, manifest and signature.

The content hash must be a SHA-256 hexadecimal digest.

## Installation boundary

The domain model does not perform package loading, installation or cryptographic verification.

The application layer defines contracts for package installation, installed package access, package catalog operations, and RulePack loading.

`MarketplaceService` delegates installation to `MarketplacePackageInstaller` and RulePack loading to `MarketplaceRulePackLoader`.

## RulePack handling

A RulePack is loaded only when the installed package is identified as `RULE_PACK`.

Loading goes through the existing RulePack loader rather than direct package execution from the domain model.

## Security boundary

Do not document or implement marketplace packages as arbitrary code that the domain layer imports and executes.

Package verification, staging, loading and infrastructure concerns belong behind the application/infrastructure contracts already defined by the repository.

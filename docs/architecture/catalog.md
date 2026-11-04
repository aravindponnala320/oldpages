# Catalog Architecture

Milestone 2 adds the `catalog` module to the modular monolith.

```text
oldpages_api/catalog/
  router.py
  schemas.py
  models.py
  repository.py
  service.py
  permissions.py
  exceptions.py
  isbn.py
  events.py
  tasks.py
```

## Boundaries

- `Book` is the canonical intellectual work.
- `BookEdition` is the edition-level record future listings should reference.
- `Author`, `Publisher`, and `Category` are reusable metadata entities.
- `BookIdentifier` stores ISBN and external identifiers.
- `AcademicMetadata` is one-to-one with an edition for school, college, exam, and course fields.

Routers only handle HTTP transport. Services own duplicate detection, ISBN normalization, metadata correction, and audit logging. Repositories own SQLAlchemy query shape and eager-loading.

## Provider Abstraction

ISBN lookup goes through `IsbnMetadataProvider`. Milestone 2 ships `LocalCatalogIsbnProvider`; later providers can fetch external metadata and return the same resolved edition contract.

## Authorization

Catalog browsing is public. Manual creation and correction require an active authenticated user as a temporary admin-correction rule. Platform-role RBAC belongs in a later admin/trust milestone.

## Search Readiness

The catalog stores normalized title, ISBNs, authors, publisher, categories, language, genres, subjects, and academic metadata so Milestone 4 can build search documents without changing the catalog schema.

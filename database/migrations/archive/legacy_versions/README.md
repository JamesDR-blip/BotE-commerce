# Archived Alembic history (inactive)

These 23 revision files retain the original content from the former active `database/migrations/versions` lineage. They are historical evidence only and are deliberately outside Alembic's configured `versions` location. They are not imported by the current Alembic script directory, are not an additional lineage, and must not be used by `upgrade head`. Checkout line endings may follow the local Git configuration.

The active clean-install path is the single root revision `20261002_01` in `database/migrations/versions/20261002_01_canonical_postgresql_baseline.py`. The archive exists because the former connected history could not deterministically bootstrap the canonical PostgreSQL 16 schema. Existing local databases with archived revision IDs are not automatically upgraded or stamped; classify, back up, fingerprint, and follow a separately approved adoption procedure.

Original archived revision IDs (23):
0001_persistence
20230912_01
20230912_02
20230912_03
20230912_04
20260914_01
20260914_02
20260914_03
20260916_01
20260916_02
20260916_03
20260916_04
20260922_01
20260923_01
20260926_01
20260928_01
7757af5afe0a
b05fd7d45c87
c13a7e91d204
d14c1f2a9b31
e2f3a4b5c6d7
f3a4b5c6d7e8
fcbc1a52044c


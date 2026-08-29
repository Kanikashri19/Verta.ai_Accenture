# Verta.ai — Evidence Store Directory

This directory houses the local ChromaDB persistent vector database (`data/vector_store/`) and evidence metadata artifacts.

- Vector database: Embedded ChromaDB with local FastEmbed embeddings (`BAAI/bge-small-en-v1.5`, 384 dimensions).
- All stored documents have PII masked prior to indexing.
- Zero cloud API calls are required; operates 100% offline.

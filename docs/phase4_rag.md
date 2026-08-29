# Verta.ai — Phase 4: Evidence Intelligence & Deterministic RAG Engine

> [!IMPORTANT]
> **No LLM is used in Phase 4.**
> All evidence retrieval, ranking, scoring, and classification (SUPPORTING vs CONTRADICTORY vs NEUTRAL) are performed strictly deterministically using mathematical scoring formulas, local dense vector embeddings, metadata filters, temporal window gating, and Role-Based Access Control (RBAC).

---

## 1. Architecture Overview & Multi-Lane Pipeline

The Verta.ai Evidence Intelligence Layer bridges quantitative KPI anomalies (from Phase 3) and qualitative unstructured operational signals (`customer_operations_events`). It operates entirely offline and locally using **FastEmbed** (`BAAI/bge-small-en-v1.5`) and a persistent **ChromaDB** vector database.

```mermaid
flowchart TD
    subgraph DataIngestion ["1. Data Ingestion & Sanitization"]
        RawEvents[Raw customer_operations_events] --> PIIMasker[PII Masking Engine\nRegex-based sanitization]
        PIIMasker --> Normalizer[Evidence Normalizer\nSchema mapping & lineage]
        Normalizer --> Chunker[Semantic Chunker\nParent-child preserving]
    end

    subgraph VectorIndexing ["2. Vector Store & Local Embeddings"]
        Chunker --> LocalEmbedder[Local FastEmbed Model\nBAAI/bge-small-en-v1.5 (384-dim)]
        LocalEmbedder --> ChromaDB[(Persistent ChromaDB\ndata/vector_store/)]
    end

    subgraph RetrievalScoring ["3. Retrieval, RBAC & Deterministic Scoring"]
        FactPack[Phase 3 FactPack / Query] --> QueryBuilder[Targeted Semantic Query Builder]
        QueryBuilder --> ChromaDB
        ChromaDB --> MultiLaneFilter[Multi-Lane Metadata Filter\nTemporal + Scenario + RBAC]
        MultiLaneFilter --> Scorer[Deterministic Scorer\n[0-100 Composite Score]]
        Scorer --> Classifier[Rule-Based Classifier\nSUPPORTING / CONTRADICTORY / NEUTRAL]
    end

    subgraph OutputDelivery ["4. Structured Output"]
        Classifier --> EvidencePack[Structured EvidencePack\nREST API & FactPack Enrichment]
    end
```

---

## 2. PII Masking Specification

Before any operational event is chunked or embedded into ChromaDB, it passes through the strict regex-based `PIIMasker` (`backend/app/evidence/pii.py`).

| PII Category | Pattern Matched | Replacement Token | Example Transformation |
| :--- | :--- | :--- | :--- |
| **Email** | Standard RFC 5322 regex | `[MASKED_EMAIL]` | `user@example.com` $\to$ `[MASKED_EMAIL]` |
| **Phone Number** | International & US formats | `[MASKED_PHONE]` | `+1-800-555-0199` $\to$ `[MASKED_PHONE]` |
| **Credit Card** | 13–19 digit Luhn-valid patterns | `[MASKED_CARD]` | `4532-1234-5678-9012` $\to$ `[MASKED_CARD]` |
| **Customer Name** | Contextual name introductions | `[MASKED_NAME]` | `Customer John Doe reported` $\to$ `Customer [MASKED_NAME] reported` |
| **IP Address** | IPv4 standard notation | `[MASKED_IP]` | `192.168.1.1` $\to$ `[MASKED_IP]` |

**Security Guarantee**: 100% of documents stored in ChromaDB have zero raw PII. This is verified by `tests/test_evidence_security.py::test_raw_pii_never_in_vector_store`.

---

## 3. Local Dense Embeddings & Vector Storage

- **Model**: `BAAI/bge-small-en-v1.5` running via the lightweight `fastembed` ONNX runtime library.
- **Embedding Dimensions**: 384-dimensional normalized dense vectors.
- **Vector Database**: Persistent `chromadb` client stored at `data/vector_store/`.
- **Zero Cloud / External Dependency**: All embeddings and vector searches execute locally offline.
- **Idempotent Ingestion**: Documents are indexed with deterministic SHA-256 hashes as IDs (`EVID-{SOURCE}-{DATE}-{HASH}`). Upsert operations prevent duplicate entries across re-indexing runs.

---

## 4. Deterministic Scoring Mathematical Formula

Every retrieved document receives a deterministic score $S \in [0, 100]$ based on five mathematical components:

$$S = 35 \cdot S_{\text{sim}} + 25 \cdot T + 15 \cdot D + 15 \cdot Sev + 10 \cdot Tag$$

Where:
1. **Semantic Similarity ($S_{\text{sim}} \in [0, 1]$)**: Cosine similarity between the query embedding and document embedding, scaled by weight $35$.
2. **Temporal Window Alignment ($T \in \{0.0, 0.5, 1.0\}$)**:
   - $T = 1.0$ if document date falls within the exact anomaly period ($[\text{start}, \text{end}]$).
   - $T = 0.5$ if document date is within $\pm 2$ days of the anomaly period (near-window).
   - $T = 0.0$ if document date is outside the window.
3. **Dimensional Match ($D \in \{0.0, 1.0\}$)**:
   - $D = 1.0$ if the document's region or product matches the investigated anomaly scope or global scope.
   - $D = 0.0$ if there is an explicit dimensional mismatch.
4. **Severity Weight ($Sev \in \{0.25, 0.50, 0.75, 1.00\}$)**:
   - `CRITICAL`: $1.00$
   - `HIGH`: $0.75$
   - `MEDIUM`: $0.50$
   - `LOW`: $0.25$
5. **Driver Tag Alignment ($Tag \in \{0.0, 1.0\}$)**:
   - $Tag = 1.0$ if document tags match the investigated driver (e.g., `PAYMENT_GATEWAY_TIMEOUT` for `conversion_rate`).
   - $Tag = 0.0$ otherwise.

---

## 5. Metadata Filtering & Evidence Classification

### Multi-Lane Classification Rules
The retrieval engine deterministically classifies evidence into three distinct buckets:
- **`SUPPORTING`**: Operational events whose driver tags, temporal window, and failure descriptions directly substantiate the quantitative anomaly (e.g., EU payment gateway timeouts during a European conversion rate drop).
- **`CONTRADICTORY`**: Operational telemetry indicating normal/healthy operation or events that contradict the quantitative hypothesis (e.g., in Scenario 5 where logistics memos indicate EU freight surcharges, but sales data shows discount promotions caused the margin compression).
- **`NEUTRAL`**: General inquiries or routine feedback within the time window that do not explain the specific driver.

### Role-Based Access Control (RBAC)
- **`EXECUTIVE`**: Restricted to high-level summaries and internal ops; **strictly forbidden** from viewing `PII_RESTRICTED` documents.
- **`ANALYST`**: Full analytical access to all operational events and masked customer support tickets.
- **`OPERATIONS`**: Direct access to operational incident logs and technical telemetry.
- **`UNAUTHORIZED`**: Blocked; returns zero evidence and `INSUFFICIENT_EVIDENCE` status.

### Ground-Truth Independence
The Evidence Intelligence Layer never inspects or references `scenarios.yaml` ground-truth sections. Retrieval is driven purely by querying the ingested event logs against the FactPack's observed KPI anomaly parameters.

---

## 6. REST API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/evidence/retrieve` | `GET` | Retrieve structured evidence for a KPI, driver, and time window with RBAC role gating. |
| `/api/evidence/enrich-factpack` | `POST` | Ingests a Phase 3 `FactPack` and returns a enriched `FactPack` with linked `EvidencePack`. |
| `/api/evidence/ingest` | `POST` | Ingests operational event data for a specified scenario into ChromaDB. |
| `/api/evidence/telemetry` | `GET` | Returns audit telemetry on retrieval counts, latencies, and RBAC enforcement. |
| `/api/evidence/mask-pii` | `POST` | Standalone utility endpoint to mask raw text with deterministic tokens. |
| `/api/evidence/status` | `GET` | Health check endpoint reporting vector store document counts and model status. |

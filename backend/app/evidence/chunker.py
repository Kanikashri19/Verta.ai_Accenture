from typing import List
from app.evidence.models import EvidenceDocument

class EvidenceChunker:
    """
    Deterministic chunking for operational evidence documents.
    Preserves document-level metadata, timestamps, and lineage.
    """

    MAX_CHUNK_CHARS = 600

    @classmethod
    def chunk_document(cls, doc: EvidenceDocument) -> List[EvidenceDocument]:
        """
        Splits a document if text exceeds MAX_CHUNK_CHARS, otherwise returns original document.
        """
        if len(doc.text) <= cls.MAX_CHUNK_CHARS:
            return [doc]

        chunks = []
        sentences = doc.text.split(". ")
        current_chunk = []
        current_len = 0
        part_idx = 1

        for sentence in sentences:
            s_len = len(sentence)
            if current_len + s_len > cls.MAX_CHUNK_CHARS and current_chunk:
                chunk_text = ". ".join(current_chunk) + "."
                chunk_doc = doc.model_copy(
                    update={
                        "evidence_id": f"{doc.evidence_id}-p{part_idx}",
                        "text": chunk_text,
                    }
                )
                chunks.append(chunk_doc)
                part_idx += 1
                current_chunk = [sentence]
                current_len = s_len
            else:
                current_chunk.append(sentence)
                current_len += s_len

        if current_chunk:
            chunk_text = ". ".join(current_chunk)
            if not chunk_text.endswith("."):
                chunk_text += "."
            chunk_doc = doc.model_copy(
                update={
                    "evidence_id": f"{doc.evidence_id}-p{part_idx}" if part_idx > 1 else doc.evidence_id,
                    "text": chunk_text,
                }
            )
            chunks.append(chunk_doc)

        return chunks

    @classmethod
    def chunk_documents(cls, docs: List[EvidenceDocument]) -> List[EvidenceDocument]:
        all_chunks = []
        for doc in docs:
            all_chunks.extend(cls.chunk_document(doc))
        return all_chunks

evidence_chunker = EvidenceChunker()

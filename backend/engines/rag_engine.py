import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
from rank_bm25 import BM25Okapi
import uuid
import os
import csv
import PyPDF2
import docx

class RAGEngine:
    def __init__(self):
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db"))
        self.chroma_client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.chroma_client.get_or_create_collection(name="base_documents")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # For keyword search (CSV / exact tabular data)
        self.bm25_corpus = []
        self.bm25_metadata = []
        self.bm25_index = None

    def process_file(self, file_path: str, filename: str):
        ext = os.path.splitext(filename)[1].lower()
        text_content = ""
        bm25_updated = False
        try:
            if ext == ".csv":
                import pandas as pd
                try:
                    df = pd.read_csv(file_path)
                    df = df.fillna("")
                except Exception as p_e:
                    print(f"Pandas failed on {file_path}, skipping: {p_e}")
                    return

                for idx, row in df.iterrows():
                    short_cells = []
                    for col_name in df.columns:
                        cell_val = str(row[col_name]).strip()
                        if not cell_val: continue
                        
                        if len(cell_val) > 150:
                            self._add_to_chroma(f"Row {idx+1} {col_name}: {cell_val}", {"source": filename, "row": idx+1, "col": str(col_name)})
                        else:
                            short_cells.append(f"{col_name}: {cell_val}")
                            
                    if short_cells:
                        row_text = f"Row {idx+1} Data -> " + " | ".join(short_cells)
                        self.bm25_corpus.append(row_text)
                        self.bm25_metadata.append({"source": filename, "row": idx+1})
                        bm25_updated = True
            
            elif ext == ".pdf":
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    text_content = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            
            elif ext == ".docx":
                doc = docx.Document(file_path)
                text_content = "\n".join([p.text for p in doc.paragraphs])
            
            elif ext == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    text_content = f.read()

            if text_content.strip():
                self._add_to_chroma(text_content, {"source": filename})
        except Exception as e:
            print(f"Failed to ingest {filename}: {e}")

        if bm25_updated and self.bm25_corpus:
            tokenized_corpus = [self._bm25_tokenize(doc) for doc in self.bm25_corpus]
            self.bm25_index = BM25Okapi(tokenized_corpus)
            print(f"BM25 index re-built online. Size: {len(self.bm25_corpus)} cells.")

    def ingest_base_documents(self):
        """Scans the base_documents folder and ingests files into appropriate engines."""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "base_documents"))
        if not os.path.exists(base_dir):
            os.makedirs(base_dir, exist_ok=True)
            return

        print(f"Ingesting documents from {base_dir}...")
        for filename in os.listdir(base_dir):
            file_path = os.path.join(base_dir, filename)
            if os.path.isfile(file_path):
                self.process_file(file_path, filename)

    def _bm25_tokenize(self, text: str):
        import re
        # Normalizes case and fuses hyphenated words (e.g. REQ-017 -> req017)
        normalized = text.lower().replace("-", "")
        return re.findall(r'\w+', normalized)

    def _add_to_chroma(self, text: str, metadata: dict):
        # Extremely basic chunking for brevity
        chunk_size = 1000
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            doc_id = f"{metadata['source']}_chunk_{i}_{uuid.uuid4()}"
            emb = self.embeddings.embed_query(chunk)
            self.collection.add(
                embeddings=[emb],
                documents=[chunk],
                metadatas=[metadata],
                ids=[doc_id]
            )

    def query_chroma(self, query_text: str, n_results: int = 5):
        import re
        # Expand query implicitly for Chroma embeddings by adding standardized variants
        expanded_query = query_text + " " + re.sub(r'(?i)\b([a-z]+)(\d+)\b', r'\1-\2', query_text).upper()
        
        emb = self.embeddings.embed_query(expanded_query)
        results = self.collection.query(
            query_embeddings=[emb],
            n_results=n_results
        )
        context = ""
        if results and 'documents' in results and len(results['documents']) > 0:
            for doc in results['documents'][0]:
                context += doc + "\n\n"
        return context

    def query_bm25(self, query_text: str, n_results: int = 10):
        if not self.bm25_index:
            return ""
        tokenized_query = self._bm25_tokenize(query_text)
        scores = self.bm25_index.get_scores(tokenized_query)
        
        # Filter out 0.0 score padding rows (which happen when corpus > n_results)
        ranked = sorted(zip(scores, self.bm25_corpus), key=lambda x: x[0], reverse=True)
        valid_docs = [doc for score, doc in ranked if score > 0]
        
        return "\n".join(valid_docs[:n_results])

    def query(self, query_text: str):
        # Hybrid fetch
        chroma_res = self.query_chroma(query_text)
        bm25_res = self.query_bm25(query_text)
        
        combined = "--- Semantic Document Results ---\n" + chroma_res + "\n--- Exact CSV Results ---\n" + bm25_res
        return combined

rag_engine = RAGEngine()

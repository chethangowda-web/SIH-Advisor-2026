"""
data_pipeline.py
Loads SIH data, creates embeddings, stores in ChromaDB vector database.
Run this ONCE before starting the server: python data_pipeline.py
"""

import json
import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import config

def load_sih_data(path: str) -> list[dict]:
    """Load SIH winners JSON data."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"✅ Loaded {len(data)} SIH projects from {path}")
    return data

def create_project_document(project: dict) -> str:
    """Create a rich text document from a project for embedding."""
    return f"""
    Title: {project['title']}
    Year: {project['year']}
    Domain: {project['domain']} - {project.get('sub_domain', '')}
    Problem: {project['problem_statement']}
    Solution: {project['solution']}
    Technologies: {', '.join(project['technologies'])}
    Impact: {project['impact']}
    Novelty: {', '.join(project.get('novelty_aspects', []))}
    Gap Solved: {project.get('gap_it_solved', '')}
    Ministry: {project.get('ministry', '')}
    """.strip()

def setup_chromadb() -> tuple[chromadb.Client, chromadb.Collection]:
    """Initialize ChromaDB client and collection."""
    os.makedirs(config.CHROMA_DB_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)
    
    # Delete existing collection if rebuilding
    try:
        client.delete_collection(config.CHROMA_COLLECTION_NAME)
        print("🗑️  Deleted existing collection for rebuild")
    except Exception:
        pass
    
    collection = client.create_collection(
        name=config.CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    print(f"✅ Created ChromaDB collection: {config.CHROMA_COLLECTION_NAME}")
    return client, collection

def embed_and_store(projects: list[dict], collection: chromadb.Collection):
    """Embed all projects and store in ChromaDB."""
    print(f"\n🔄 Loading embedding model: {config.EMBEDDING_MODEL}")
    model = SentenceTransformer(config.EMBEDDING_MODEL)
    
    documents = []
    embeddings = []
    metadatas = []
    ids = []
    
    print("\n🔄 Generating embeddings...")
    for project in tqdm(projects):
        doc_text = create_project_document(project)
        embedding = model.encode(doc_text).tolist()
        
        documents.append(doc_text)
        embeddings.append(embedding)
        ids.append(project["id"])
        metadatas.append({
            "id": project["id"],
            "year": project["year"],
            "title": project["title"],
            "domain": project["domain"],
            "sub_domain": project.get("sub_domain", ""),
            "is_hardware": str(project.get("is_hardware", False)),
            "ministry": project.get("ministry", ""),
            "award": project.get("award", ""),
            "technologies": ", ".join(project["technologies"]),
        })
    
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    print(f"\n✅ Stored {len(projects)} projects in ChromaDB!")

def run_pipeline():
    """Run the full data pipeline."""
    print("=" * 60)
    print("🚀 SIH AI Advisor — Data Pipeline")
    print("=" * 60)
    
    # Step 1: Load data
    projects = load_sih_data(config.DATA_PATH)
    
    # Step 2: Setup ChromaDB
    client, collection = setup_chromadb()
    
    # Step 3: Embed and store
    embed_and_store(projects, collection)
    
    # Step 4: Verify
    count = collection.count()
    print(f"\n✅ Pipeline complete! {count} projects indexed in ChromaDB")
    print(f"📁 Database saved at: {config.CHROMA_DB_PATH}")
    
    return client, collection

if __name__ == "__main__":
    run_pipeline()

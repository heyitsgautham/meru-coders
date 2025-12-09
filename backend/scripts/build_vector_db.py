"""
Build Vector Database for RAG System
Preprocesses meter data, documentation, and examples for semantic search

Usage:
    python scripts/build_vector_db.py [--rebuild]
    
Author: Meru Coders (SIH 2025)
Date: December 9, 2025
"""

import os
import sys
import json
import csv
import re
from pathlib import Path
from typing import List, Dict, Any
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
DOCS_DIR = Path(__file__).parent.parent.parent / "docs"
CHROMA_DIR = DATA_DIR / "chroma_db"
PROCESSED_DIR = DATA_DIR / "processed"

# Embedding model (multilingual for Sanskrit/Devanagari support)
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# Chunking parameters
CHUNK_SIZE = 500  # tokens
CHUNK_OVERLAP = 50  # tokens


class VectorDBBuilder:
    """Builds vector database from various knowledge sources"""
    
    def __init__(self, rebuild: bool = False):
        """
        Initialize the builder
        
        Args:
            rebuild: If True, deletes existing database and rebuilds from scratch
        """
        self.rebuild = rebuild
        self.documents: List[Document] = []
        
        # Create directories
        PROCESSED_DIR.mkdir(exist_ok=True)
        
        if rebuild and CHROMA_DIR.exists():
            print(f"🗑️  Deleting existing database at {CHROMA_DIR}")
            import shutil
            shutil.rmtree(CHROMA_DIR)
        
        # Initialize embeddings
        print(f"📦 Loading embedding model: {EMBEDDING_MODEL}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},  # Use 'cuda' if GPU available
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize text splitter for documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
    
    def process_meter_csv(self, csv_path: Path, category: str) -> int:
        """
        Process a meter CSV file into documents
        
        Args:
            csv_path: Path to CSV file
            category: Category name (sama, vishama, vedic, etc.)
        
        Returns:
            Number of documents created
        """
        print(f"📊 Processing {csv_path.name} ({category})")
        count = 0
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Extract fields (handle different CSV structures)
                    meter_name = row.get('वृत्त', row.get('chanda', ''))
                    pattern = row.get('लक्षण (raw)', row.get('pattern', ''))
                    syllables = row.get('अक्षरसङ्ख्या', row.get('syllables', ''))
                    matra = row.get('मात्रा', row.get('matra', ''))
                    yati = row.get('यति', row.get('yati', ''))
                    pada = row.get('पद', '')
                    
                    if not meter_name or not pattern:
                        continue
                    
                    # Create content for embedding
                    content = f"""Meter: {meter_name}
Category: {category}
L-G Pattern: {pattern}
Syllables: {syllables}
Matra: {matra}"""
                    
                    if yati:
                        content += f"\nYati: {yati}"
                    if pada:
                        content += f"\nPada: {pada}"
                    
                    # Create document with metadata
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": csv_path.name,
                            "type": "meter_definition",
                            "category": category,
                            "meter_name": meter_name,
                            "pattern": pattern,
                            "syllables": syllables,
                            "matra": matra
                        }
                    )
                    
                    self.documents.append(doc)
                    count += 1
        
        except Exception as e:
            print(f"⚠️  Error processing {csv_path.name}: {e}")
        
        return count
    
    def process_examples_json(self, json_path: Path) -> int:
        """
        Process examples.json into documents
        
        Args:
            json_path: Path to examples JSON file
        
        Returns:
            Number of documents created
        """
        print(f"📝 Processing {json_path.name}")
        count = 0
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            examples = data if isinstance(data, list) else data.get('examples', [])
            
            for example in examples:
                verse = example.get('verse', example.get('text', ''))
                meter = example.get('meter', example.get('chanda', ''))
                source = example.get('source', 'Unknown')
                
                if not verse or not meter:
                    continue
                
                content = f"""Example Verse:
{verse}

Identified Meter: {meter}
Source: {source}"""
                
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": json_path.name,
                        "type": "example_verse",
                        "meter": meter,
                        "text_source": source,
                        "verse": verse
                    }
                )
                
                self.documents.append(doc)
                count += 1
        
        except Exception as e:
            print(f"⚠️  Error processing {json_path.name}: {e}")
        
        return count
    
    def process_documentation(self, doc_path: Path) -> int:
        """
        Process markdown/text documentation into chunked documents
        
        Args:
            doc_path: Path to documentation file
        
        Returns:
            Number of chunks created
        """
        print(f"📖 Processing {doc_path.name}")
        count = 0
        
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip empty files
            if not content.strip():
                return 0
            
            # Extract title from first line or filename
            lines = content.split('\n')
            title = lines[0].strip('#').strip() if lines else doc_path.stem
            
            # Determine document type
            doc_type = "documentation"
            if "rule" in doc_path.name.lower():
                doc_type = "rules"
            elif "vedic" in doc_path.name.lower() or "vedanga" in doc_path.name.lower():
                doc_type = "vedic_reference"
            elif "tutorial" in doc_path.name.lower() or "course" in doc_path.name.lower():
                doc_type = "tutorial"
            
            # Split into chunks
            chunks = self.text_splitter.split_text(content)
            
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": doc_path.name,
                        "type": doc_type,
                        "title": title,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                )
                
                self.documents.append(doc)
                count += 1
        
        except Exception as e:
            print(f"⚠️  Error processing {doc_path.name}: {e}")
        
        return count
    
    def process_bhagavad_gita_csv(self, csv_path: Path) -> int:
        """
        Process Bhagavad Gita verses CSV
        
        Args:
            csv_path: Path to Bhagavad Gita CSV file
        
        Returns:
            Number of documents created
        """
        print(f"🕉️  Processing {csv_path.name}")
        count = 0
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    verse = row.get('verse', row.get('text', ''))
                    meter = row.get('meter', row.get('chanda', ''))
                    chapter = row.get('chapter', '')
                    verse_num = row.get('verse_number', '')
                    
                    if not verse:
                        continue
                    
                    content = f"""Bhagavad Gita - Chapter {chapter}, Verse {verse_num}:
{verse}

Meter: {meter}
Source: Bhagavad Gita"""
                    
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": csv_path.name,
                            "type": "sacred_text_example",
                            "meter": meter,
                            "text_source": "Bhagavad Gita",
                            "chapter": chapter,
                            "verse_number": verse_num
                        }
                    )
                    
                    self.documents.append(doc)
                    count += 1
        
        except Exception as e:
            print(f"⚠️  Error processing {csv_path.name}: {e}")
        
        return count
    
    def build_database(self):
        """Build the complete vector database"""
        print("\n" + "="*60)
        print("🚀 Building Vector Database for RAG System")
        print("="*60 + "\n")
        
        total_docs = 0
        
        # 1. Process meter CSV files
        print("📊 STEP 1: Processing Meter Definitions")
        print("-" * 60)
        
        meter_files = [
            ("chanda_sama.csv", "sama"),
            ("chanda_vishama.csv", "vishama"),
            ("chanda_vedic.csv", "vedic"),
            ("chanda_matra.csv", "matra"),
            ("chanda_jaati.csv", "jaati"),
            ("chanda_ardhasama.csv", "ardhasama"),
        ]
        
        for filename, category in meter_files:
            path = DATA_DIR / filename
            if path.exists():
                count = self.process_meter_csv(path, category)
                total_docs += count
                print(f"  ✅ Added {count} documents from {filename}")
            else:
                print(f"  ⚠️  Skipped {filename} (not found)")
        
        # 2. Process example verses
        print("\n📝 STEP 2: Processing Example Verses")
        print("-" * 60)
        
        examples_path = DATA_DIR / "examples.json"
        if examples_path.exists():
            count = self.process_examples_json(examples_path)
            total_docs += count
            print(f"  ✅ Added {count} documents from examples.json")
        
        # 3. Process Bhagavad Gita
        gita_path = DATA_DIR / "bhagavad_gita_verses.csv"
        if gita_path.exists():
            count = self.process_bhagavad_gita_csv(gita_path)
            total_docs += count
            print(f"  ✅ Added {count} documents from Bhagavad Gita")
        
        # 4. Process documentation files
        print("\n📖 STEP 3: Processing Documentation")
        print("-" * 60)
        
        doc_files = [
            "chandas_rules.md",
            "chandas_as_vedanga.txt",
            "chandovallari.txt",
            "meter.md",
            "List_Vedic_Chandas.md",
            "7_vedic_chandas_showcase.md",
            "online_course_resource.md"
        ]
        
        for filename in doc_files:
            path = DOCS_DIR / filename
            if path.exists():
                count = self.process_documentation(path)
                total_docs += count
                print(f"  ✅ Added {count} chunks from {filename}")
            else:
                print(f"  ⚠️  Skipped {filename} (not found)")
        
        # 5. Create vector store
        print(f"\n🔨 STEP 4: Building Vector Store")
        print("-" * 60)
        print(f"Total documents to embed: {total_docs}")
        
        if total_docs == 0:
            print("❌ No documents to process. Exiting.")
            return
        
        print(f"📦 Generating embeddings using {EMBEDDING_MODEL}...")
        print("⏳ This may take several minutes...")
        
        vectorstore = Chroma.from_documents(
            documents=self.documents,
            embedding=self.embeddings,
            persist_directory=str(CHROMA_DIR),
            collection_name="chandas_knowledge"
        )
        
        print(f"✅ Vector store created with {vectorstore._collection.count()} documents")
        
        # 6. Save summary
        summary = {
            "total_documents": total_docs,
            "embedding_model": EMBEDDING_MODEL,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "categories": {
                "meter_definitions": len([d for d in self.documents if d.metadata.get("type") == "meter_definition"]),
                "example_verses": len([d for d in self.documents if d.metadata.get("type") == "example_verse"]),
                "sacred_texts": len([d for d in self.documents if d.metadata.get("type") == "sacred_text_example"]),
                "documentation": len([d for d in self.documents if d.metadata.get("type") in ["documentation", "rules", "vedic_reference", "tutorial"]])
            }
        }
        
        summary_path = PROCESSED_DIR / "build_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Summary saved to {summary_path}")
        print("\n" + "="*60)
        print("✅ Vector Database Build Complete!")
        print("="*60)
        print(f"\n📍 Location: {CHROMA_DIR}")
        print(f"📈 Total Documents: {total_docs}")
        print(f"🔍 Embedding Dimensions: 768")
        print(f"\n🎯 Next Steps:")
        print("  1. Run: python -m backend.core.rag_engine (to test retrieval)")
        print("  2. Integrate with chatbot API")
        print("  3. Test end-to-end RAG pipeline")


def main():
    parser = argparse.ArgumentParser(description="Build vector database for RAG system")
    parser.add_argument('--rebuild', action='store_true', help='Rebuild database from scratch')
    args = parser.parse_args()
    
    builder = VectorDBBuilder(rebuild=args.rebuild)
    builder.build_database()


if __name__ == "__main__":
    main()

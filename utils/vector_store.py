import os
import uuid
import re
from typing import List, Dict, Any, Optional

class VectorStore:
    """
    Fallback vector store implementation that works without Milvus
    Uses in-memory storage with file persistence
    """
    def __init__(self):
        self.host = os.getenv('MILVUS_HOST', 'localhost')
        self.port = os.getenv('MILVUS_PORT', '19530')
        self.collections = {}
        self.storage_dir = 'vector_storage'
        self.milvus_available = False
        
        # Try to connect to Milvus first
        try:
            self._try_milvus_connection()
        except Exception as e:
            print(f"⚠️  Milvus not available, using fallback storage: {e}")
            self._init_fallback_storage()

    def _try_milvus_connection(self):
        """Try to connect to Milvus"""
        try:
            from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
            
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            print("✅ Connected to Milvus successfully")
            self.milvus_available = True
            
            # Import Milvus modules for later use
            self.connections = connections
            self.Collection = Collection
            self.CollectionSchema = CollectionSchema
            self.FieldSchema = FieldSchema
            self.DataType = DataType
            self.utility = utility
            
        except ImportError:
            print("⚠️  Milvus library not installed, using fallback storage")
            raise Exception("Milvus library not available")
        except Exception as e:
            print(f"⚠️  Cannot connect to Milvus: {e}")
            raise e

    def _init_fallback_storage(self):
        """Initialize fallback file-based storage"""
        os.makedirs(self.storage_dir, exist_ok=True)
        print("✅ Initialized fallback vector storage")

    def _format_collection_name(self, session_id):
        safe_id = re.sub(r'[^a-zA-Z0-9_]', '', session_id)
        return f"sess_{safe_id}"

    def create_collection_schema(self):
        """Create collection schema for Milvus"""
        if not self.milvus_available:
            return None
            
        fields = [
            self.FieldSchema(name="id", dtype=self.DataType.VARCHAR, max_length=100, is_primary=True),
            self.FieldSchema(name="text", dtype=self.DataType.VARCHAR, max_length=5000),
            self.FieldSchema(name="original_text", dtype=self.DataType.VARCHAR, max_length=10000),
            self.FieldSchema(name="filename", dtype=self.DataType.VARCHAR, max_length=255),
            self.FieldSchema(name="embedding", dtype=self.DataType.FLOAT_VECTOR, dim=768)
        ]
        return self.CollectionSchema(fields=fields, description="Document embeddings collection")

    def create_collection(self, session_id):
        """Create collection (Milvus or fallback)"""
        collection_name = self._format_collection_name(session_id)
        
        if self.milvus_available:
            try:
                if self.utility.has_collection(collection_name):
                    return self.Collection(collection_name)

                schema = self.create_collection_schema()
                collection = self.Collection(collection_name, schema)

                index_params = {
                    "index_type": "IVF_FLAT",
                    "metric_type": "COSINE",
                    "params": {"nlist": 1024}
                }
                collection.create_index(field_name="embedding", index_params=index_params)
                return collection
            except Exception as e:
                print(f"❌ Error creating Milvus collection: {str(e)}")
                self.milvus_available = False
                return self._create_fallback_collection(collection_name)
        else:
            return self._create_fallback_collection(collection_name)

    def _create_fallback_collection(self, collection_name):
        """Create fallback collection"""
        if collection_name not in self.collections:
            self.collections[collection_name] = {
                'documents': [],
                'metadata': {
                    'created_at': str(uuid.uuid4()),
                    'name': collection_name
                }
            }
            self._save_collection_to_file(collection_name)
        return collection_name

    def _save_collection_to_file(self, collection_name):
        """Save collection to file"""
        try:
            import json
            file_path = os.path.join(self.storage_dir, f"{collection_name}.json")
            with open(file_path, 'w') as f:
                json.dump(self.collections[collection_name], f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving collection to file: {e}")

    def _load_collection_from_file(self, collection_name):
        """Load collection from file"""
        try:
            import json
            file_path = os.path.join(self.storage_dir, f"{collection_name}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    self.collections[collection_name] = json.load(f)
                return True
        except Exception as e:
            print(f"⚠️  Error loading collection from file: {e}")
        return False

    def collection_exists(self, session_id):
        """Check if collection exists"""
        collection_name = self._format_collection_name(session_id)
        
        if self.milvus_available:
            try:
                return self.utility.has_collection(collection_name)
            except Exception as e:
                print(f"❌ Error checking Milvus collection existence: {str(e)}")
                self.milvus_available = False
        
        # Fallback check
        return (collection_name in self.collections or 
                os.path.exists(os.path.join(self.storage_dir, f"{collection_name}.json")))

    def add_documents(self, session_id, documents, filename):
        """Add documents to collection"""
        collection_name = self._format_collection_name(session_id)
        
        if self.milvus_available:
            try:
                collection = self.create_collection(session_id)

                ids = []
                texts = []
                original_texts = []
                filenames = []
                embeddings = []

                for doc in documents:
                    ids.append(str(uuid.uuid4()))
                    texts.append(doc['text'])
                    original_texts.append(doc['original_text'])
                    filenames.append(filename)
                    embeddings.append(doc['embedding'])

                data = [ids, texts, original_texts, filenames, embeddings]
                collection.insert(data)
                collection.flush()
                collection.load()

                print(f"✅ Added {len(documents)} documents to Milvus collection {collection_name}")
                return True
            except Exception as e:
                print(f"❌ Error adding documents to Milvus: {str(e)}")
                self.milvus_available = False
        
        # Fallback to file storage
        return self._add_documents_fallback(collection_name, documents, filename)

    def _add_documents_fallback(self, collection_name, documents, filename):
        """Add documents using fallback storage"""
        try:
            if collection_name not in self.collections:
                if not self._load_collection_from_file(collection_name):
                    self._create_fallback_collection(collection_name)

            for doc in documents:
                document_entry = {
                    'id': str(uuid.uuid4()),
                    'text': doc['text'],
                    'original_text': doc['original_text'],
                    'filename': filename,
                    'embedding': doc['embedding']
                }
                self.collections[collection_name]['documents'].append(document_entry)

            self._save_collection_to_file(collection_name)
            print(f"✅ Added {len(documents)} documents to fallback collection {collection_name}")
            return True
        except Exception as e:
            print(f"❌ Error adding documents to fallback storage: {str(e)}")
            return False

    def search_documents(self, session_id, query_text, top_k=5):
        """Search documents in collection"""
        collection_name = self._format_collection_name(session_id)
        
        if self.milvus_available:
            try:
                if not self.utility.has_collection(collection_name):
                    return []

                collection = self.Collection(collection_name)
                collection.load()

                # Get query embedding
                query_embedding = self._get_query_embedding(query_text)
                if not query_embedding:
                    return []

                search_params = {
                    "metric_type": "COSINE",
                    "params": {"nprobe": 10}
                }

                results = collection.search(
                    data=[query_embedding],
                    anns_field="embedding",
                    param=search_params,
                    limit=top_k,
                    output_fields=["text", "original_text", "filename"]
                )

                documents = []
                for result in results[0]:
                    documents.append({
                        'text': result.entity.get('text'),
                        'original_text': result.entity.get('original_text'),
                        'filename': result.entity.get('filename'),
                        'score': result.score
                    })

                return documents
            except Exception as e:
                print(f"❌ Error searching Milvus documents: {str(e)}")
                self.milvus_available = False
        
        # Fallback search
        return self._search_documents_fallback(collection_name, query_text, top_k)

    def _search_documents_fallback(self, collection_name, query_text, top_k=5):
        """Search documents using fallback storage"""
        try:
            if collection_name not in self.collections:
                if not self._load_collection_from_file(collection_name):
                    return []

            query_embedding = self._get_query_embedding(query_text)
            if not query_embedding:
                return []

            documents = self.collections[collection_name]['documents']
            scored_docs = []

            for doc in documents:
                try:
                    # Calculate cosine similarity
                    score = self._cosine_similarity(query_embedding, doc['embedding'])
                    scored_docs.append({
                        'text': doc['text'],
                        'original_text': doc['original_text'],
                        'filename': doc['filename'],
                        'score': score
                    })
                except Exception as e:
                    print(f"⚠️  Error calculating similarity: {e}")
                    continue

            # Sort by score and return top_k
            scored_docs.sort(key=lambda x: x['score'], reverse=True)
            return scored_docs[:top_k]

        except Exception as e:
            print(f"❌ Error searching fallback documents: {str(e)}")
            return []

    def _get_query_embedding(self, query_text):
        """Get embedding for query text"""
        try:
            from utils.document_processor import DocumentProcessor
            doc_processor = DocumentProcessor()
            return doc_processor.get_embedding(query_text)
        except Exception as e:
            print(f"❌ Error getting query embedding: {str(e)}")
            return None

    def _cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        try:
            import numpy as np
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            print(f"❌ Error calculating cosine similarity: {str(e)}")
            return 0

    def delete_collection(self, session_id):
        """Delete collection"""
        collection_name = self._format_collection_name(session_id)
        
        if self.milvus_available:
            try:
                if self.utility.has_collection(collection_name):
                    self.utility.drop_collection(collection_name)
                    print(f"🧹 Deleted Milvus collection {collection_name}")
            except Exception as e:
                print(f"❌ Error deleting Milvus collection: {str(e)}")
                self.milvus_available = False
        
        # Fallback deletion
        try:
            if collection_name in self.collections:
                del self.collections[collection_name]
            
            file_path = os.path.join(self.storage_dir, f"{collection_name}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            
            print(f"🧹 Deleted fallback collection {collection_name}")
            return True
        except Exception as e:
            print(f"❌ Error deleting fallback collection: {str(e)}")
            return False

    def get_collection_stats(self, session_id):
        """Get collection statistics"""
        collection_name = self._format_collection_name(session_id)
        
        if self.milvus_available:
            try:
                if not self.utility.has_collection(collection_name):
                    return None

                collection = self.Collection(collection_name)
                collection.load()

                return {
                    'name': collection_name,
                    'num_entities': collection.num_entities,
                    'description': collection.description,
                    'storage_type': 'milvus'
                }
            except Exception as e:
                print(f"❌ Error getting Milvus collection stats: {str(e)}")
                self.milvus_available = False
        
        # Fallback stats
        try:
            if collection_name not in self.collections:
                if not self._load_collection_from_file(collection_name):
                    return None

            return {
                'name': collection_name,
                'num_entities': len(self.collections[collection_name]['documents']),
                'description': 'Fallback vector storage',
                'storage_type': 'file'
            }
        except Exception as e:
            print(f"❌ Error getting fallback collection stats: {str(e)}")
            return None
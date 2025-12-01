"""
Admin panel routes for the Graph RAG web UI.
"""

import os
import sys
from pathlib import Path
from flask import Blueprint, render_template, jsonify
from dotenv import load_dotenv

load_dotenv()

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

admin_bp = Blueprint('admin', __name__)


def get_qdrant_stats():
    """Get statistics from Qdrant."""
    try:
        from qdrant_client import QdrantClient
        
        qdrant_url = f"{os.getenv('QDRANT_URL')}:{os.getenv('QDRANT_HTTP_PORT', '6333')}"
        client = QdrantClient(url=qdrant_url)
        
        collection_name = "QdrantRagCollection"
        try:
            collection = client.get_collection(collection_name)
            return {
                "status": "connected",
                "collection": collection_name,
                "vectors_count": collection.vectors_count,
                "points_count": collection.points_count,
                "segments_count": collection.segments_count if hasattr(collection, 'segments_count') else 0,
            }
        except Exception:
            return {
                "status": "connected",
                "collection": None,
                "vectors_count": 0,
                "points_count": 0,
                "segments_count": 0,
            }
    except Exception as e:
        return {
            "status": "disconnected",
            "error": str(e)
        }


def get_neo4j_stats():
    """Get statistics from Neo4j."""
    try:
        from neo4j import GraphDatabase
        
        neo4j_url = f"{os.getenv('NEO4J_URL')}:{os.getenv('NEO4J_BOLT_PORT')}"
        neo4j_auth = tuple(os.getenv("NEO4J_AUTH").split("/"))
        
        driver = GraphDatabase.driver(neo4j_url, auth=neo4j_auth)
        
        with driver.session() as session:
            # Count nodes
            entity_count = session.run("MATCH (n:Entity) RETURN count(n) as count").single()["count"]
            chunk_count = session.run("MATCH (n:Chunk) RETURN count(n) as count").single()["count"]
            
            # Count relationships
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
            mentions_count = session.run("MATCH ()-[r:MENTIONS]->() RETURN count(r) as count").single()["count"]
        
        driver.close()
        
        return {
            "status": "connected",
            "entity_nodes": entity_count,
            "chunk_nodes": chunk_count,
            "total_relationships": rel_count,
            "mentions_relationships": mentions_count,
        }
    except Exception as e:
        return {
            "status": "disconnected",
            "error": str(e)
        }


def get_ollama_status():
    """Check Ollama status."""
    try:
        import requests
        
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            return {
                "status": "connected",
                "models": models,
                "model_count": len(models)
            }
        else:
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "status": "disconnected",
            "error": str(e)
        }


@admin_bp.route('/admin')
def admin_page():
    """Render the admin panel."""
    qdrant_stats = get_qdrant_stats()
    neo4j_stats = get_neo4j_stats()
    ollama_stats = get_ollama_status()
    
    return render_template('admin.html',
                          qdrant=qdrant_stats,
                          neo4j=neo4j_stats,
                          ollama=ollama_stats)


@admin_bp.route('/api/stats')
def get_stats():
    """API endpoint to get all stats."""
    return jsonify({
        "qdrant": get_qdrant_stats(),
        "neo4j": get_neo4j_stats(),
        "ollama": get_ollama_status()
    })


@admin_bp.route('/api/clear-data', methods=['POST'])
def clear_data():
    """Clear all data from databases."""
    results = {"qdrant": None, "neo4j": None}
    
    # Clear Qdrant
    try:
        from qdrant_client import QdrantClient
        
        qdrant_url = f"{os.getenv('QDRANT_URL')}:{os.getenv('QDRANT_HTTP_PORT', '6333')}"
        client = QdrantClient(url=qdrant_url)
        
        collection_name = "QdrantRagCollection"
        try:
            client.delete_collection(collection_name)
            results["qdrant"] = {"success": True, "message": "Collection deleted"}
        except Exception:
            results["qdrant"] = {"success": True, "message": "Collection not found"}
    except Exception as e:
        results["qdrant"] = {"success": False, "error": str(e)}
    
    # Clear Neo4j
    try:
        from neo4j import GraphDatabase
        
        neo4j_url = f"{os.getenv('NEO4J_URL')}:{os.getenv('NEO4J_BOLT_PORT')}"
        neo4j_auth = tuple(os.getenv("NEO4J_AUTH").split("/"))
        
        driver = GraphDatabase.driver(neo4j_url, auth=neo4j_auth)
        
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        driver.close()
        results["neo4j"] = {"success": True, "message": "All nodes and relationships deleted"}
    except Exception as e:
        results["neo4j"] = {"success": False, "error": str(e)}
    
    return jsonify(results)


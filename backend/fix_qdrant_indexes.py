"""Fix Qdrant collection by adding required payload indexes."""
import sys
from app.config import settings
from app.ingestion import get_qdrant_client
from qdrant_client.models import PayloadSchemaType

def fix_indexes():
    """Add payload indexes to existing collection."""
    print("="*80)
    print("FIXING QDRANT COLLECTION INDEXES")
    print("="*80)
    
    collection_name = settings.qdrant_collection
    print(f"\nCollection: {collection_name}")
    
    try:
        client = get_qdrant_client()
        print("✅ Connected to Qdrant")
        
        # Check if collection exists
        try:
            collection = client.get_collection(collection_name)
            print(f"✅ Collection exists with {collection.points_count} points")
        except Exception as e:
            print(f"❌ Collection not found: {e}")
            print("\nPlease upload a document first to create the collection.")
            return False
        
        # Create user_id index
        print("\n📊 Creating payload index for 'user_id'...")
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name="user_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            print("✅ Created user_id index")
        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                print("⚠️  user_id index already exists")
            else:
                print(f"❌ Failed to create user_id index: {e}")
                return False
        
        # Create document_id index
        print("\n📊 Creating payload index for 'document_id'...")
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name="document_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            print("✅ Created document_id index")
        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                print("⚠️  document_id index already exists")
            else:
                print(f"❌ Failed to create document_id index: {e}")
                return False
        
        # Verify indexes
        print("\n🔍 Verifying collection info...")
        collection_info = client.get_collection(collection_name)
        print(f"✅ Collection has {collection_info.points_count} points")
        
        if hasattr(collection_info, 'payload_schema'):
            print(f"✅ Payload schema: {collection_info.payload_schema}")
        
        print("\n" + "="*80)
        print("🎉 SUCCESS! Indexes created successfully")
        print("="*80)
        print("\nYou can now:")
        print("  1. Restart your backend server")
        print("  2. Try querying documents again")
        print("  3. The 'user_id' filter will now work efficiently")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_indexes()
    sys.exit(0 if success else 1)

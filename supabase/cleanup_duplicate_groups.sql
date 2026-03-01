-- Cleanup script for duplicate document group memberships
-- This removes duplicate entries where a document appears in multiple groups
-- Keeps only the first membership for each document

-- Step 1: Create a temporary table with the memberships to keep (first one per document)
CREATE TEMP TABLE memberships_to_keep AS
SELECT DISTINCT ON (document_id) id
FROM document_group_membership
ORDER BY document_id, added_at ASC;

-- Step 2: Delete all memberships that are NOT in the keep list
DELETE FROM document_group_membership
WHERE id NOT IN (SELECT id FROM memberships_to_keep);

-- Step 3: Show summary
SELECT 
    'Cleanup complete' as status,
    COUNT(DISTINCT document_id) as unique_documents,
    COUNT(*) as total_memberships
FROM document_group_membership;

-- Optional: Show current group distribution
SELECT 
    dg.group_name,
    dg.group_type,
    COUNT(dgm.document_id) as document_count
FROM document_groups dg
LEFT JOIN document_group_membership dgm ON dg.id = dgm.group_id
GROUP BY dg.id, dg.group_name, dg.group_type
ORDER BY dg.group_type, dg.group_name;

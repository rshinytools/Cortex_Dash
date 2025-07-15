-- ABOUTME: SQL script to manually clean up draft studies from the database
-- ABOUTME: Use this to remove incomplete draft studies if needed

-- View all draft studies
SELECT id, name, protocol_number, status, created_at, created_by 
FROM study 
WHERE status IN ('draft', 'DRAFT')
ORDER BY created_at DESC;

-- Delete a specific draft study by ID (replace with actual ID)
-- DELETE FROM study WHERE id = 'study-id-here' AND status IN ('draft', 'DRAFT');

-- Delete all draft studies older than 7 days
-- DELETE FROM study 
-- WHERE status IN ('draft', 'DRAFT') 
-- AND created_at < NOW() - INTERVAL '7 days';

-- Delete all draft studies for a specific user (replace with user ID)  
-- DELETE FROM study 
-- WHERE status IN ('draft', 'DRAFT')
-- AND created_by = 'user-id-here';
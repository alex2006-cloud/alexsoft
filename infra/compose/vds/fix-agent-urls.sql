UPDATE bl.agents
SET config = jsonb_set(config::jsonb, '{url}', '"http://agent1:2024"', true)
WHERE id IN ('bp1-project-qa', 'agent1-qa');
SELECT id, config FROM bl.agents WHERE id IN ('bp1-project-qa', 'agent1-qa');

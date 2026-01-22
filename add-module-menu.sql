-- Add Module Management menu item to No-Code Platform menu
-- Run this SQL script against your database

-- First, find the No-Code Platform parent menu ID
DO $$
DECLARE
    nocode_menu_id UUID;
    new_menu_id UUID;
BEGIN
    -- Get the No-Code Platform menu ID
    SELECT id INTO nocode_menu_id
    FROM menu_items
    WHERE name = 'No-Code Platform'
    LIMIT 1;

    IF nocode_menu_id IS NULL THEN
        RAISE NOTICE 'No-Code Platform menu not found. Creating it...';

        -- Create No-Code Platform parent menu if it doesn't exist
        INSERT INTO menu_items (id, name, path, icon, position, is_active, created_at)
        VALUES (
            gen_random_uuid(),
            'No-Code Platform',
            NULL,
            'cube',
            100,
            true,
            NOW()
        )
        RETURNING id INTO nocode_menu_id;
    END IF;

    -- Check if Module Management already exists
    IF NOT EXISTS (
        SELECT 1 FROM menu_items
        WHERE name = 'Module Management'
        AND parent_id = nocode_menu_id
    ) THEN
        -- Add Module Management menu item
        new_menu_id := gen_random_uuid();

        INSERT INTO menu_items (
            id,
            parent_id,
            name,
            path,
            icon,
            position,
            is_active,
            created_at,
            description
        ) VALUES (
            new_menu_id,
            nocode_menu_id,
            'Module Management',
            '/nocode-modules.html',
            'package',
            5,
            true,
            NOW(),
            'Create and manage business domain modules'
        );

        RAISE NOTICE 'Module Management menu item created successfully!';
        RAISE NOTICE 'Menu ID: %', new_menu_id;
    ELSE
        RAISE NOTICE 'Module Management menu item already exists';
    END IF;
END $$;

-- Verify the menu was added
SELECT
    mi.id,
    mi.name,
    mi.path,
    mi.icon,
    mi.position,
    parent.name as parent_menu
FROM menu_items mi
LEFT JOIN menu_items parent ON mi.parent_id = parent.id
WHERE mi.name = 'Module Management'
ORDER BY mi.position;

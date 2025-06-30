import sys
import os
sys.path.append('restaurant_management_api')

from restaurant_management_api.src.models import db, ChefDishMapping, Chef, Item
from restaurant_management_api.src.main import create_app

app = create_app()

with app.app_context():
    # Check total chef mappings
    total_mappings = ChefDishMapping.query.count()
    print(f"Total Chef Mappings: {total_mappings}")
    
    # Check chef mappings for specific tenant
    tenant_id = '31a6a0fa-3d86-4b03-ad26-44503189d3d4'
    tenant_mappings = ChefDishMapping.query.filter_by(tenant_id=tenant_id).count()
    print(f"Chef Mappings for tenant {tenant_id}: {tenant_mappings}")
    
    # Check all chefs
    total_chefs = Chef.query.count()
    print(f"Total Chefs: {total_chefs}")
    
    # Check chefs for specific tenant
    tenant_chefs = Chef.query.filter_by(tenant_id=tenant_id).count()
    print(f"Chefs for tenant {tenant_id}: {tenant_chefs}")
    
    # Check all items
    total_items = Item.query.count()
    print(f"Total Items: {total_items}")
    
    # Check items for specific tenant
    tenant_items = Item.query.filter_by(tenant_id=tenant_id).count()
    print(f"Items for tenant {tenant_id}: {tenant_items}")
    
    # Show some sample mappings
    print("\nSample Chef Mappings:")
    mappings = ChefDishMapping.query.limit(5).all()
    for mapping in mappings:
        chef = Chef.query.get(mapping.chef_id)
        item = Item.query.get(mapping.item_id)
        print(f"  Mapping {mapping.id}: Chef '{chef.name if chef else 'Unknown'}' -> Item '{item.name if item else 'Unknown'}' (Tenant: {mapping.tenant_id})")

    # Ensure default 'Unassigned' chef exists
    unassigned_chef = Chef.query.filter_by(name='Unassigned').first()
    if not unassigned_chef:
        unassigned_chef = Chef(clover_id='unassigned', name='Unassigned', is_active=True)
        db.session.add(unassigned_chef)
        db.session.commit()
        print("Created default 'Unassigned' chef.")
    else:
        print("Default 'Unassigned' chef already exists.")

    # Find all items not mapped in ChefDishMapping
    mapped_item_ids = set(m.item_id for m in ChefDishMapping.query.all())
    unmapped_items = Item.query.filter(~Item.id.in_(mapped_item_ids)).all()
    print(f"Unmapped items: {len(unmapped_items)}")

    # Create mappings for unmapped items
    created_count = 0
    for item in unmapped_items:
        mapping = ChefDishMapping(chef_id=unassigned_chef.id, item_id=item.id, is_active=True)
        db.session.add(mapping)
        created_count += 1
    if created_count > 0:
        db.session.commit()
    print(f"Created {created_count} new mappings to 'Unassigned' chef.") 
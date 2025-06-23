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
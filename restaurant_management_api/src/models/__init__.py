from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Import models after db is initialized
from .user import User
from .item import Item
from .sale import Sale
from .chef import Chef
from .chef_dish_mapping import ChefDishMapping
from .expense import Expense
from .category import Category
from .uncategorized_item import UncategorizedItem
from .file_upload import FileUpload
from .tenant import Tenant

# Export models
__all__ = [
    'db',
    'User',
    'Item',
    'Sale',
    'Chef',
    'ChefDishMapping',
    'Expense',
    'Category',
    'UncategorizedItem',
    'FileUpload',
    'Tenant'
] 
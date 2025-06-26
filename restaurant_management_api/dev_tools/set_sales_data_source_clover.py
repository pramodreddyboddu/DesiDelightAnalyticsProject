from dotenv import load_dotenv
load_dotenv()

from src.main import create_app
from src.models import db
from src.models.data_source_config import DataSourceConfig

app = create_app()
with app.app_context():
    config = DataSourceConfig.query.filter_by(tenant_id=None, data_type='sales').first()
    if not config:
        config = DataSourceConfig(tenant_id=None, data_type='sales', source='clover', updated_by='admin')
    else:
        config.source = 'clover'
        config.updated_by = 'admin'
    db.session.add(config)
    db.session.commit()
    print('Sales data source set to clover.')

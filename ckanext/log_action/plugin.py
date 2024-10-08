import logging
from typing import Any, Mapping, Optional, Union, cast
import ckan.plugins as plugins
import uuid
import json
from datetime import datetime
from sqlalchemy import Table, Column, String, DateTime, MetaData
from ckan.plugins import implements, SingletonPlugin
from ckan.plugins.toolkit import config
from ckan.model import meta
from ckan.plugins.interfaces import IAuthenticator, IPackageController, IResourceView, IDatasetForm
from ckan.types import Context
from flask_login import current_user as _cu

from ckan.types.model import Model
current_user = cast(Union["Model.User", "Model.AnonymousUser"], _cu)
log = logging.getLogger(__name__)


class LogActionPlugin(plugins.SingletonPlugin):
    implements(IAuthenticator, inherit=True)
    implements(IResourceView, inherit=True)
    implements(IPackageController, inherit=True)

    def _get_log_table(self):
        engine = meta.engine
        metadata = MetaData(bind=engine)
        log_table = Table(
            'log_actions',
            metadata,
            Column('id', String, primary_key=True),
            Column('log_date', DateTime),
            Column('user_name', String),
            Column('action_name', String),
            Column('action_type', String),
            Column('details', String),
        )
        metadata.create_all(engine)
        return log_table

    def _log_action(self, user_name: Optional[String], action_name:String, 
                    action_type: Optional[String] =None, 
                    details: Optional[Any]=None):
        log_table = self._get_log_table()
        insert = log_table.insert().values(
            id=str(uuid.uuid4()),
            log_date=datetime.utcnow(),
            user_name=user_name,
            action_name=action_name,
            action_type=action_type,
            details=json.dumps(details)
        )
        meta.engine.execute(insert) # type: ignore

    # def authenticate(self, identity: Mapping[str, Any]):
    #     user_name = data_dict.get('name')
    #     success = True  # Check authentication result here
    #     status = 'pass' if success else 'fail'
    #     self._log_action(
    #         user_name=user_name,
    #         action_name='authentication',
    #         details={'status': status}
    #     )
    #     return success
    def after_dataset_show(self,context: Context, dataset_dict:dict[str, Any])-> None:
        log.debug('add log action')
        log.debug(context)
        user = None
        if current_user.is_authenticated:
            user = current_user.name
        self._log_action(
            user_name=user,
            action_name='dataset',
            action_type='view',
            details={'dataset_id': dataset_dict['id']}
        )
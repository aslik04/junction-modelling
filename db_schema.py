from flask_sqlalchemy import SQLAlchemy #, ForeignKey
from flask_login import UserMixin

from werkzeug import security
import datetime
from sqlalchemy.inspection import inspect

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


# create the database interface
db = SQLAlchemy()


    # tables = inspect(db.engine).get_table_names()
    # if len(tables) > 0:
    #     print(f"The database contains these tables already\n{tables}" )
    #     return
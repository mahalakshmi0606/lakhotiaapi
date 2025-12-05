import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI',
        'mysql+mysqldb://root:root123@localhost/lakhotia'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
   
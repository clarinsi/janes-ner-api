import sys, os

helperspath = os.path.realpath('../src/')
sys.path.append(helperspath)

import unittest
import os
import sys
from datetime import datetime, timedelta
from helpers import to_unix_timestamp

modelsPath = os.path.realpath('../src/models')
sys.path.append(modelsPath)

dbPath = os.path.realpath('../src/db')
sys.path.append(dbPath)

from users_db import UsersDB
from auth_token_model import AuthTokenModel

class AuthTokenModelTests(unittest.TestCase):

    # Runs once per class
    @classmethod
    def setUpClass(cls):
        UsersDB.getInstance().reset()  

    def test_create_token(self):
        token_string = 'kksdfsdfsdjfjsdkfj9887'
        timestamp = datetime.now()
        token = AuthTokenModel()
        token.user_id = 33
        token.token = token_string
        token.expiration_timestamp = timestamp
        token.updated = timestamp
        token.created = timestamp
        token.save()
    
        dbTokenRow = AuthTokenModel.getByAttributeSingle('token', token_string)
    
        self.assertEqual(dbTokenRow.user_id, 33)
        self.assertEqual(dbTokenRow.token, token_string)
        self.assertEqual(dbTokenRow.expiration_timestamp, timestamp)    
        #self.assertEqual(dbTokenRow.updated, timestamp)
        #self.assertEqual(dbTokenRow.created, timestamp)

    def test_is_valid_true(self):
        tok = 'klowekoriweruuiweryu6767'
        timestamp = datetime.now()
        token = AuthTokenModel()
        token.user_id = 36
        token.token = tok
        token.expiration_timestamp = timestamp + timedelta(days = 1) + timedelta(hours = 2)
        token.save()
    
        dbTokenRow = AuthTokenModel.getByAttributeSingle('token',tok)    
        

        self.assertEqual(dbTokenRow.isValid(), True)
        
    def test_is_valid_false(self):
        tok = 'ksejfiwejir873487347567'
        timestamp = datetime.now()
        token = AuthTokenModel()
        token.user_id = 36
        token.token = tok
        token.expiration_timestamp = timestamp + timedelta(days = -1) + timedelta(hours = 2)
        token.save()
    
        dbTokenRow = AuthTokenModel.getByAttributeSingle('token',tok)    
        
        self.assertEqual(dbTokenRow.isValid(), False)
    
    def test_is_valid_when_times_are_equal(self):
        tok = '8645u6hjrthgjhretjhgjh'
        timestamp = datetime.now()
        token = AuthTokenModel()
        token.user_id = 37
        token.token = tok
        token.expiration_timestamp = timestamp
        token.save()
    
        dbTokenRow = AuthTokenModel.getByAttributeSingle('token',tok)    
        
        #koga expiration date e ednakvo momentalnoto vreme, dava deka tokenot ne e validen, dali treba da e taka?
        self.assertEqual(dbTokenRow.isValid(), False)
        
    def test_extend(self):
        tok = '9458893457874587huhghbdfhg'
        timestamp = datetime.now()
        token = AuthTokenModel()
        token.user_id = 38
        token.token = tok
        token.expiration_timestamp = timestamp + timedelta(hours = 1)
        token.save()
    
        dbTokenRow = AuthTokenModel.getByAttributeSingle('token',tok)    
        #ovde javuva greska : TypeError: unsupported operand type(s) for +: 'datetime.datetime' and 'int' - debagirano
        dbTokenRow.extend() #ova go konvertira expiration_timestamp vo unix time
        self.assertTrue(dbTokenRow.isValid()) #expiration_timestamp e vekje unix timestamp i ne moze da napravi sporedba, dokolku od extend se trgne to_unix_timestamp raboti dobro
    
    def test_generate(self):
        tok = 'ksdkfksdjf77w3647673'
        timestamp = datetime.now()
        token = AuthTokenModel()
        token.user_id = 39
        token.token = tok
        token.expiration_timestamp = timestamp + timedelta(hours = 1)
        token.save()
        
        dbTokenRow = AuthTokenModel.getByAttributeSingle('token', tok)
        new_token = AuthTokenModel.generate(dbTokenRow.isLongLasting())

        dbTokenRow.token = new_token.token
        # if dt.tzinfo is not None:AttributeError: 'NoneType' object has no attribute 'tzinfo' 
        dbTokenRow.expiration_timestamp = new_token.expiration_timestamp
        dbTokenRow.save()
        
        dbTokenRow = AuthTokenModel.getByAttributeSingle('token',new_token.token)
        self.assertEqual(dbTokenRow.token, new_token.token)
        self.assertEqual(dbTokenRow.expiration_timestamp, new_token.expiration_timestamp)   
        self.assertEqual(dbTokenRow.isLongLasting(), False)
        
if __name__ == '__main__':
    unittest.main()

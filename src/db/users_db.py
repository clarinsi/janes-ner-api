
# -*- coding: utf-8 -*-
import os
import sqlite3
import sys

srcPath = os.path.realpath('../')
sys.path.append(srcPath)
from janes_ner_db import DB

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class UsersDB(DB):
    '''Serves as a database access layer for the users database. This class is a singleton'''
    # Stores the connection
    _instance = None

    @staticmethod
    def getInstance():
        """
        Returns the singleton database access instance.
        """
        assetsPath = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/../../assets/')

        databaseName = assetsPath + '/users';
        if (UsersDB._instance is None):
            UsersDB._instance = UsersDB(DB._THE_MAGIC_WORD)
            if (UsersDB._instance._connection is None):
                # Initialize connection
                UsersDB._instance._connection = sqlite3.connect(databaseName,isolation_level=None)
                UsersDB._instance._connection.text_factory = str
                UsersDB._instance._connection.row_factory = dict_factory
                UsersDB._instance._client = UsersDB._instance._connection.cursor()

            UsersDB._instance.__createTables()

        return UsersDB._instance

    def getInsertId(self):
        """
        Returns the id of the last inserted record.
        """
        return self._client.lastrowid

    def reset(self):
        """
        Resets / refreshes the users database by dropping and recreating all tables
        """

        self.command("DROP TABLE IF EXISTS users")
        self.command("DROP TABLE IF EXISTS auth_tokens")
        self.__createTables()

    def __createTables(self):
        """
        Creates the tables used to storing users
        """
        db = self.getInstance()
        # Create users table
        statement = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                project TEXT,
                requests_limit INTEGER NOT NULL,
                note TEXT,
                requests_made INTEGER NOT NULL DEFAULT 0,
                last_request_datetime TEXT,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                updated TEXT NOT NULL,
                created TEXT NOT NULL,
                activation_token TEXT,
                password_reset_token TEXT,
                password_reset_expiration_token TEXT,
                CHECK (role IN ("admin", "user"))
                CHECK (status IN ("pending", "blocked", "active", "not-verified"))
            );
        """
        db.command(statement)

        # Create tokens table
        statement = """
            CREATE TABLE IF NOT EXISTS auth_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT,
                expiration_timestamp TEXT,
                updated TEXT NOT NULL,
                created TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
                UNIQUE(user_id, token)
            );
        """
        db.command(statement)

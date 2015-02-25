#!/usr/bin/python
# -*- coding: utf-8 -*-

import psycopg2
import psycopg2.extras

class DatabaseError(Exception):
    pass
class NotFoundError(Exception):
    pass

class Entity(object):
    db = None
        # ORM part 1
    __delete_query    = 'DELETE FROM "{table}" WHERE {table}_id=%s'
    __insert_query    = 'INSERT INTO "{table}" ({columns}) VALUES ({placeholders}) RETURNING "{table}_id"'
    __list_query      = 'SELECT * FROM "{table}"'
    __select_query    = 'SELECT * FROM "{table}" WHERE {table}_id=%s'
    __update_query    = 'UPDATE "{table}" SET {columns} WHERE {table}_id=%s'

    # ORM part 2
    __parent_query    = 'SELECT * FROM "{table}" WHERE {parent}_id=%s'
    __sibling_query   = 'SELECT * FROM "{sibling}" NATURAL JOIN "{join_table}" WHERE {table}_id=%s'
    __update_children = 'UPDATE "{table}" SET {parent}_id=%s WHERE {table}_id IN ({children})'

    __all_loaded = None

    def __init__(self, id=None):
        if self.__class__.db is None:
            raise DatabaseError()
        # self.__cursor   = self.__class__.db.cursor()
        # self.__cursor   = self.__class__.db.cursor(
        #     cursor_factory=psycopg2.extras.DictCursor
        # )
        self.__cursor   = self.__class__.db.cursor(
            cursor_factory = psycopg2.extras.RealDictCursor
        )
        self.__fields   = {}
        self.__id       = id
        self.__loaded   = False
        self.__modified = False
        self.__table    = self.__class__.__name__.lower()

    def __getattr__(self, name):
        if (self.__id is not None) and (self.__loaded is False):
        # if (self.__loaded == False):
            self.__load()

        # if name in self.__fields.keys():
            # return self.__fields[name]
        if name in self._fields:
            return self.__fields[self.__table + "_" + name]
        else:
            raise AttributeError("can not set invalid attribute")

    def __setattr__(self, name, value):
        if (name in self._fields):
            if (self.__loaded == False):
                self.__load()
            self.__fields[self.__table + "_" + name] =  value
            self.__modified = True
        else:
            super(Entity, self).__setattr__(name, value)

    def __execute_query(self, query, args):
        # execute an sql statement and handle exceptions together with transactions
        if args == None:
            self.__cursor.execute(query)
        else:
            try:
                self.__cursor.execute(query, args, )
                Entity.db.commit()
            except Exception, err:
                print err

        # try:
        #     self.__cursor.execute(query, args, )
        #     Entity.db.commit()
        # except Exception, err:
        #     print err

    def __insert(self):
        # generate an insert query string from fields keys and values and execute it
        # use prepared statements
        # save an insert id
        if self.__id != None:
            self.__fields[self.__table + "_id"] = self.__id
        column = ", ".join(self.__fields.keys())
        placeholder = list()
        for elem in xrange(len(self.__fields)):
            placeholder.append('%s')
        placeholder = ", ".join(placeholder)
        insert_query    = self.__insert_query.format(table = self.__table, columns = column, placeholders = placeholder)
        self.__execute_query(insert_query, self.__fields.values())

    def __load(self):
        # for elem in self._fields:# if current instance is not loaded yet — execute select statement 
        # and store it's result as an associative array (fields), where column names used as keys
        # self.loaded = True
       
        select_query = self.__select_query.format(table = self.__table)
        self.__execute_query(select_query, (self.__id, ))

        bd_data = self.__cursor.fetchone()
        if bd_data == None:
            return
        else:
            self.__fields = bd_data
        self.__loaded = True
 

    def __update(self):
        # generate an update query string from fields keys and values and execute it
        # use prepared statements
        new_keys = [elem+'=%s' for elem in self.__fields.keys()]
        column = ", ".join(new_keys)
        update_query    = self.__update_query.format(table = self.__table, columns = column)
        fields_values = list(self.__fields.values())
        fields_values.append(self.id)
        self.__execute_query(update_query, fields_values)

    def _get_children(self, name):
        # return an array of child entity instances
        # each child instance must have an id and be filled with data
        pass

    def _get_column(self, name):
        # return value from fields array by <table>_<name> as a key
        pass

    def _get_parent(self, name):
        # get parent id from fields with <name>_id as a key
        # return an instance of parent entity class with an appropriate id
        pass

    def _get_siblings(self, name):
        # get parent id from fields with <name>_id as a key
        # return an array of sibling entity instances
        # each sibling instance must have an id and be filled with data
        pass

    def _set_column(self, name, value):
        # put new value into fields array with <table>_<name> as a key
        pass

    def _set_parent(self, name, value):
        # put new value into fields array with <name>_id as a key
        # value can be a number or an instance of Entity subclass
        pass

    @classmethod
    def all(cls):
        # get ALL rows with ALL columns from corrensponding table
        # for each row create an instance of appropriate class
        # each instance must be filled with column data, a correct id and MUST NOT query a database for own fields any more
        # return an array of istances
        # list_query = Entity.__list_query.format(table = "article")
        list_query = Entity.__list_query.format(table = cls.__name__.lower())
        cursor   = Entity.db.cursor(
            cursor_factory = psycopg2.extras.RealDictCursor
        )
        # Entity.__execute_query(entity, list_query)
        try:
            cursor.execute(list_query)
        except Exception, err:
            print err
        columns = [column[0] for column in cursor.description]
        db_list = {}
        bd_data = cursor.fetchall()
        if bd_data == None:
            return
        else:
            pass
        instance_list = []
        for  elem in bd_data:
            instance = super(Entity, cls).__new__(cls)
            cls.__init__(instance)
            instance.__id = elem[cls.__name__.lower() + '_id']
            instance.__fields = elem
            instance.__loaded = True
            instance.__modified = False
            instance_list.append(instance)

        return instance_list

    def delete(self):
        # execute delete query with appropriate id
        if self.__id == None:
            raise NotFoundError()
        delete_query = self.__delete_query.format(table = self.__table)
        self.__execute_query(delete_query, (self.id, ))

    @property
    def id(self):
        return self.__id

    @property
    def created(self):
        # try to guess yourself
        return self.__fields[self.__table+"_created"]

    @property
    def updated(self):
        # try to guess yourself
        return self.__fields[self.__table+"_updated"]

    def save(self):
        # execute either insert or update query, depending on instance id
        if self.__modified == True:
            if (self.__loaded == True) and (self.__id != None):
                self.__update()
            else:
                self.__insert()
        else:
            pass
        self.__modified = False

if __name__ == "__main__":
    pass

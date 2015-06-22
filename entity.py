#!/usr/bin/python
# -*- coding: utf-8 -*-

import psycopg2
import psycopg2.extras
import pprint

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

    def __init__(self, id=None):
        if self.__class__.db is None:
            raise DatabaseError()
        self.__cursor   = self.__class__.db.cursor(
            cursor_factory = psycopg2.extras.RealDictCursor
        )
        self.__fields   = {}
        self.__id       = id
        self.__loaded   = False
        self.__modified = False
        self.__table    = self.__class__.__name__.lower()

    def __getattr__(self, name):
        self.__load()
        if name in self._siblings:
            return self._get_siblings(self._siblings[name])
        elif name in self._children:
            return self._get_children(self._children[name])
        elif name in self._parents:
            return self._get_parent(name)
        elif name in self._fields:
            return self._get_column(name)
        else:
            return AttributeError()

    def __setattr__(self, name, value):
        if name in self._parents:
            self._set_parent(name,value)
        elif name in self._fields:
            self._set_column(name, value)
        else:
            super(Entity, self).__setattr__(name, value)

    def __execute_query(self, query, args):
        try:
            self.__cursor.execute(query, args)
            Entity.db.commit()
        except psycopg2.Error, err:
            Entity.db.rollback()
            print"Error in query:", query
            print err

    def __insert(self):
        if self.__id != None:
            self.__fields['{}_id'.format(self.__table)] = self.__id

        column = ", ".join(self.__fields.keys())
        placeholder = ", ".join(['%s'] * len(self.__fields))

        insert_query    = self.__insert_query.format(table = self.__table, columns = column, placeholders = placeholder)
        self.__execute_query(insert_query, self.__fields.values())

    def __load(self):
        if self.__loaded is False:
            select_query = self.__select_query.format(table = self.__table)
            self.__execute_query(select_query, (self.__id, ))

            db_data = self.__cursor.fetchone()
            if db_data == None:
                return
            else:
                self.__fields = db_data
            self.__loaded = True
 
    def __update(self):
        new_keys = ("{}=%s".format(elem) for elem in self.__fields)
        column = ", ".join(new_keys)
        update_query = self.__update_query.format(table = self.__table, columns = column)
        fields_values = self.__fields.values()
        fields_values.append(self.id)

        self.__execute_query(update_query, fields_values)

    def _get_children(self, name):
        import models

        cls = getattr(models, name)
        cls_object = cls(self.__id)
        super(Entity, self).__setattr__(name, cls_object)

        cursor = cls.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            parent_query = cls.__parent_query.format(table = cls.__name__.lower(), parent = self.__table)
            cursor.execute(parent_query, (self.__id, ))
            Entity.db.commit()
        except psycopg2.Error, err:
            print"Error in query:", query
            print err
        
        key_id = "{}_id".format(cls.__name__.lower())
        for elem in cursor:
            instance = cls()
            instance.__fields = dict(elem)
            instance.__id = elem[key_id]
            yield instance

    def _get_column(self, name):
        return self.__fields['{}_{}'.format(self.__table, name)]

    def _get_parent(self, name ):
        import models
        parent_id = self.__fields['{}_id'.format(name)]
        cls = getattr(models, name.title())
        cls_object = cls(parent_id)
        super(Entity, self).__setattr__(name, cls_object)
        return cls_object

    def _get_siblings(self, name):
        import models

        cls = getattr(models, name)
        cls_object = cls(self.__id)
        super(Entity, self).__setattr__(name, cls_object)

        cursor = cls.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            relation_m_to_m_table = '{table}__{sibling}'.format(table=self.__table, sibling=cls.__name__.lower())
            sibling_query = cls.__sibling_query.format(sibling=cls.__name__.lower(), join_table=relation_m_to_m_table, \
                                                       table=self.__table)
            cursor.execute(sibling_query, (self.__id, ))
            Entity.db.commit()
        except Exception, err:
            Entity.db.rollback()
            try:
                another_m_to_m_table = '{sibling}__{table}'.format(table=self.__table, sibling=cls.__name__.lower())
                sibling_query = cls.__sibling_query.format(sibling=cls.__name__.lower(), join_table=another_m_to_m_table, \
                                                           table=self.__table)
                cursor.execute(sibling_query, (self.__id, ))
                Entity.db.commit()
            except Exception, err:
                print"Error in query:", query
                print err
            
        key_id = "{}_id".format(cls.__name__.lower())
        for elem in cursor:
            instance = cls()
            instance.__fields = dict(elem)
            instance.__id = elem[key_id]
            yield instance

    def _set_column(self, name, value):
        self.__fields['{}_{}'.format(self.__table, name)] =  value
        self.__modified = True

    def _set_parent(self, name, value):
        import models

        if (name.title() == value.__class__.__name__):
            self.__fields['{}_id'.format(name)] =  value.id
            parent = self._get_parent(name)
            self.__modified = True
        elif isinstance(value, int):
            self.__fields['{}_id'.format(name)] =  value
            parent = self._get_parent(name)
            self.__modified = True
        else:
            return AttributeError()

    @classmethod
    def all(cls):
        cursor = cls.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute(cls.__parent_query.format(table = cls.__name__.lower(), ))
            Entity.db.commit()
        except psycopg2.Error, err:
            print"Error in query:", query
            print err
        
        key_id = "{}_id".format(cls.__name__.lower())
        for elem in cursor:
            instance = cls()
            instance.__fields = dict(elem)
            instance.__id = elem[key_id]
            yield instance

    def delete(self):
        if self.__id == None:
            raise NotFoundError()

        delete_query = self.__delete_query.format(table = self.__table)
        self.__execute_query(delete_query, (self.id, ))

    @property
    def id(self):
        return self.__id

    @property
    def created(self):
        time = "{}_created".format(self.__table)
        if time in self.__fields:
            return self.__fields[time]

    @property
    def updated(self):
        time = "{}_updated".format(self.__table)
        if time in self.__fields:
            return self.__fields[time]

    def save(self):
        if self.__modified == True:
            if self.__id != None:
                self.__update()
            else:
                self.__insert()
        self.__modified = False

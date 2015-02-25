#!/usr/bin/python
# -*- coding: utf-8 -*-

# import psycopg2

from entity import *

class Article(Entity):
    _fields = ['title', 'content']

class Section(Entity):
    _columns  = ['title']
    _parents  = []
    _children = {'categories': 'Category'}
    _siblings = {}

class Category(Entity):
    _columns  = ['title']
    _parents  = ['section']
    _children = {'posts': 'Post'}
    _siblings = {}

class Post(Entity):
    _columns  = ['content', 'title']
    _parents  = ['category']
    _children = {'comments': 'Comment'}
    _siblings = {'tags': 'Tag'}

class Comment(Entity):
    _columns  = ['text']
    _parents  = ['post', 'user']
    _children = {}
    _siblings = {}

class Tag(Entity):
    _columns  = ['name']
    _parents  = []
    _children = {}
    _siblings = {'posts': 'Post'}

class User(Entity):
    _columns  = ['name', 'email', 'age']
    _parents  = []
    _children = {'comments': 'Comment'}
    _siblings = {}


if __name__ == "__main__":

    Entity.db = psycopg2.connect("dbname='orm' user='orm' host='127.0.0.1' password='orm'")

    for article in Article.all():
        print(str(article.id) + '  ' + article.title + '  ' + article.content)

    article = Article()
    article.title = 'xxxxxx'
    article.content = 'alex is alive!!!'
    article.save()

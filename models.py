#!/usr/bin/python
# -*- coding: utf-8 -*-

# import psycopg2
import pprint
from entity import *

class Article(Entity):
   _fields   = ['title', 'text']
   _parents  = ['category']
   _children = {}
   _siblings = {'tags': 'Tag'}
   
   
class Category(Entity):
   _fields   = ['title']
   _parents  = []
   _children = {'articles': 'Article'}
   _siblings = {}
   
   
class Tag(Entity):
   _fields   = ['value']
   _parents  = []
   _children = {}
   _siblings = {'articles': 'Article'}

# class Section(Entity):
#     _columns  = ['title']
#     _parents  = []
#     _children = {'categories': 'Category'}
#     _siblings = {}

# class Category(Entity):
#     _columns  = ['title']
#     _parents  = ['section']
#     _children = {'posts': 'Post'}
#     _siblings = {}

# class Post(Entity):
#     _columns  = ['content', 'title']
#     _parents  = ['category']
#     _children = {'comments': 'Comment'}
#     _siblings = {'tags': 'Tag'}

# class Comment(Entity):
#     _columns  = ['text']
#     _parents  = ['post', 'user']
#     _children = {}
#     _siblings = {}

# class Tag(Entity):
#     _columns  = ['name']
#     _parents  = []
#     _children = {}
#     _siblings = {'posts': 'Post'}

# class User(Entity):
#     _columns  = ['name', 'email', 'age']
#     _parents  = []
#     _children = {'comments': 'Comment'}
#     _siblings = {}


if __name__ == "__main__":

    Entity.db = psycopg2.connect("dbname='g2' user='g2' host='127.0.0.1' password='g2'")
    # Entity.db = psycopg2.connect("dbname='o2' user='o2' host='127.0.0.1' password='o2'")

    category = Category(2)
    for article in category.articles: # select * from article where category_id=?
        print('{} {}'.format(article.title, str(article.id)))


    article = Article(1)
    for tag in article.tags: # select * from tag natural join article_tag where article_id=?
        print('{} {}'.format(article.title, tag.value))

    tag = Tag(1)
    for article in tag.articles:
        print('{} {}'.format(article.title, tag.value))

    tag = Tag(1)
    for post in tag.posts:
        print(post.title)
   
    print article.category.title
    article.category = 2
    print article.category.title
    article.save()

    category1 = Category(1)
    article.category = category1
    article.save()
    print article.category.title

        
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import Cookie
import os
import collections
from cgi import parse_qs, escape

def application(environ, start_response):

    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0

    if '/get/' in environ["REQUEST_URI"]:
        response_body = do_get(environ)
        response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(response_body)))]

    elif '/post/' in environ["REQUEST_URI"]:
        response_body = do_post(environ, request_body_size)
        response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(response_body)))]

    elif '/cookie/' in environ["REQUEST_URI"]:
        with open('html_cookie.html', 'r') as get_file:
            html_cookie = get_file.read()

        if 'HTTP_COOKIE' in environ:
            cookie = Cookie.SimpleCookie(environ['HTTP_COOKIE'])
            page_visit = int(cookie['visit'].value) + 1
            cookie['visit'] = str(page_visit)
            response_body = 'page visits = {}'.format(cookie['visit'].value)
            response_headers = [
                                ('Content-Type', 'text/html'),
                                ('Set-Cookie', 'visit={}'.format(str(page_visit)))
            ]
        else:
            cookie = Cookie.SimpleCookie()
            page_visit = 1
            cookie['visit'] = '1'
            response_body = 'page visits = {}'.format(cookie['visit'].value)
            response_headers = [
                                ('Content-Type', 'text/html'),
                                ('Set-Cookie', 'visit={}'.format(str(page_visit)))
            ]
    else:
        response_body = "Hello python!"
        response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(response_body)))]

    status = '200 OK'
    start_response(status, response_headers)

    return [response_body]

def do_get(environ):
    environ_dict = parse_qs(environ['QUERY_STRING'])
    table_td = ''
    for k,v in environ_dict.items():
        table_td +='''<tr>
    <td style="padding: 5px; border: 1px solid black; border-collapse: collapse;">{}</td>
    <td style="padding: 5px; border: 1px solid black; border-collapse: collapse;">{}</td>    
</tr>'''.format(k, v[0])
        
    with open('html_get.html', 'r') as cookie_file:
        html_get = cookie_file.read()
    return html_get.format(table_td)

def do_post(environ, request_body_size):
    request_body = environ['wsgi.input'].read(request_body_size)
    environ_dict = parse_qs(request_body)
    if environ['REQUEST_METHOD'] == 'GET':
        with open('html_post.html', 'r') as post_file:
            html_post = post_file.read()
        return html_post
    else:
        with open('html_post1.html', 'r') as post_file:
            name = ''
            sex = ''
            education = ''
            comment = ''
            get_spam = 'нет'
            html_post = post_file.read()
        if 'Имя' in environ_dict:
            name = environ_dict['Имя'][0]
        if 'Пол' in environ_dict:
            sex = environ_dict['Пол'][0]
        if 'Образование' in environ_dict:
            education = environ_dict['Образование'][0]
        if 'Комментарий' in environ_dict:
            comment = environ_dict['Комментарий'][0]
        if 'Получать спам' in environ_dict:
            get_spam = environ_dict['Получать спам'][0]
        return html_post.format(name, sex, education, comment, get_spam)
    return "Hello python!"
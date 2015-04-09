# -*- coding: utf-8 -*-
import sqlite3, re


class Base(object):
    data = []

    def __init__(self, source):
        self.source = source

    def get(self):
        return self.data

    def read(self):
        raise NotImplementedError('Not implemented yet')


class Kindle(Base):
    def read(self):
        conn = sqlite3.connect(self.source)
        for row in conn.execute('SELECT word FROM WORDS;'):
            if isinstance(row[0], unicode):
                self.data.append(row[0])
        conn.close()


class Text(Base):
    def read(self):
        f = open(self.source)
        lines = f.readlines()
        self.data = []
        rx = r'[^A-Za-z\']+'
        #rx = r'[\s,\.:;“”\?]+'
        for l in lines:
            self.data +=  [w for w in re.split(rx, l) if len(w)]
        f.close()

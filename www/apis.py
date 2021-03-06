#!/usr/bin/python

""" json api definition """

# import json
# import logging
# import inspect
# import funtools

_PAGE_SIZE = 10  # 每页条数


class APIError(Exception):
    def __init__(self, error, data='', message=''):
        super().__init__(message)
        self.error = error
        self.data = data
        self.message = message


class APIValueError(APIError):
    def __init__(self, field, message=''):
        super().__init__('value:invalid', field, message)


class APIResourceNotFoundError(APIError):
    def __init__(self, field, message=''):
        super().__init__('value:NotFound', field, message)


class APIPermissionError(APIError):
    def __init__(self, message=''):
        super().__init__('permission:forbidden', 'permission', message)


class Page(object):
    """ 分页 """
    def __init__(self, item_count, page_index=1, page_size=_PAGE_SIZE):
        self.item_count = item_count
        self.page_size = page_size
        self.page_count = item_count // page_size + (
            1 if item_count % page_size > 0 else 0
        )
        if (item_count == 0) or (page_index > self.page_count):
            self.offset = 0
            self.limit = 0
            self.page_index = 1
        else:
            self.page_index = page_index
            self.offset = self.page_size * (page_index - 1)
            self.limit = self.page_size

        self.has_next = self.page_index < self.page_count
        self.has_prev = self.page_index > 1

    def __str__(self):

        return "item_count: {0}, page_count: {1}, page_index: {2}, "\
            "page_size: {3}, offset: {4}, limit: {5}".format(
                self.item_count,
                self.page_count,
                self.page_index,
                self.page_size,
                self.offset,
                self.limit
            )

    __repr__ = __str__

#!/usr/bin/python
# coding:utf-8
import wechat.CacheFunc as x


def test_token():
    return x.get_access_token()


if __name__ == '__main__':
    print(test_token())
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在线获取股票名称的多种方案
"""

import requests
import json

def fetch_from_sina_api(stock_code):
    """
    方案1：使用新浪财经API获取单个股票名称
    """
    try:
        # 判断市场
        if stock_code.startswith('6'):
            market = 'sh'
        else:
            market = 'sz'
        
        url = f"http://hq.sinajs.cn/list={market}{stock_code}"
        response = requests.get(url, timeout=3)
        
        if response.status_code == 200:
            data = response.text
            if 'var hq_str_' in data:
                # 解析数据
                info = data.split('"')[1].split(',')
                if len(info) > 0 and info[0]:
                    return info[0]  # 股票名称
    except:
        pass
    return None

def fetch_from_tencent_api(stock_code):
    """
    方案2：使用腾讯财经API
    """
    try:
        if stock_code.startswith('6'):
            market = 'sh'
        else:
            market = 'sz'
        
        url = f"http://qt.gtimg.cn/q={market}{stock_code}"
        response = requests.get(url, timeout=3)
        
        if response.status_code == 200:
            data = response.text
            if '~' in data:
                parts = data.split('~')
                if len(parts) > 1:
                    return parts[1]  # 股票名称
    except:
        pass
    return None

def fetch_from_eastmoney_api(stock_code):
    """
    方案3：使用东方财富API
    """
    try:
        if stock_code.startswith('6'):
            market_code = f"1.{stock_code}"
        else:
            market_code = f"0.{stock_code}"
        
        url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={market_code}&fields=f58"
        response = requests.get(url, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                return data['data'].get('f58')
    except:
        pass
    return None

# 测试
if __name__ == '__main__':
    test_code = '600000'
    print(f"测试股票代码: {test_code}")
    print(f"新浪API: {fetch_from_sina_api(test_code)}")
    print(f"腾讯API: {fetch_from_tencent_api(test_code)}")
    print(f"东方财富API: {fetch_from_eastmoney_api(test_code)}")

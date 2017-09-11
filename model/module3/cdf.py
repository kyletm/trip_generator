#!/usr/bin/python
# -*- coding: utf-8 -*-

'''Create Cumulative Distribution'''


def cdf(weights):
    total = sum(weights)
    result = []
    cumsum = 0
    for w in weights:
        cumsum += w
        if cumsum == 0:
        	result.append(0)
        else:
        	result.append(cumsum / total)
    return result

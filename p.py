#!/usr/bin/env python

import pstats

s = pstats.Stats("profile")
s.sort_stats('time').print_stats()

#!/usr/bin/env python3
import os
import sys
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from main import main

if __name__ == "__main__":
    main()
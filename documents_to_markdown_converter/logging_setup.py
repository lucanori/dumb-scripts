#!/usr/bin/env python3
import logging
import sys
from pathlib import Path

def setup_logging(log_level=logging.INFO):
    logger = logging.getLogger("slides_to_md")
    logger.setLevel(log_level)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger

def get_logger():
    return logging.getLogger("slides_to_md")
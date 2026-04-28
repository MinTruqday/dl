#!/bin/bash
export MONGODB_URI='mongodb://localhost:27017/doclib'
export REDIS_URI='redis://localhost:6379/0'
export AGENTIC_RAG_URL='http://localhost:8100'
export PYTHONPATH=$PYTHONPATH:.
pytest tests/ -v -s

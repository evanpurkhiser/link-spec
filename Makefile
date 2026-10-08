.PHONY: test test-python test-research

test: test-python

test-python:
	cd conformance && python3 -m unittest test_conformance_backend.py test_protocol_runner.py test_replay_rbxport.py

test-research:
	cd conformance && ../.venv/bin/python -m unittest discover -p 'test_*.py'

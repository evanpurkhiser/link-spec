.PHONY: test test-python test-research smoke-vynull conformance-vynull

test: test-python

test-python:
	cd conformance && python3 -m unittest test_conformance_backend.py test_protocol_runner.py test_replay_rbxport.py

test-research:
	cd conformance && ../.venv/bin/python -m unittest discover -p 'test_*.py'

smoke-vynull:
	python3 conformance/replay_vynull.py --enable-vynull-replay --suite xdj-rx3/empty

conformance-vynull:
	python3 conformance/replay_vynull.py --enable-vynull-replay

run: .env
	. .env/bin/activate; python3 -m validator

.env: .env/touchfile

.env/touchfile: requirements.txt
	test -d venv || python3 -m venv .env
	. .env/bin/activate; pip install -Ur requirements.txt
	touch .env/touchfile

clean:
	rm platforms-report.json || true

deep-clean: clean
	rm -rf .env .env/touchfile || true
	rm platforms-osm.json || true
	rm stations-osm.json || true
	rm -rf __pycache__ || true
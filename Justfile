set shell := ["bash", "-cu"]

sync:
	uv sync --all-groups

run:
	uv run python manage.py runserver 0.0.0.0:8000

migrate:
	uv run python manage.py migrate

makemigrations:
	uv run python manage.py makemigrations

lint:
	uv run ruff check .
	uv run black --check .
	uv run flake8 .

format:
	uv run black .
	uv run ruff check --fix .

type:
	uv run mypy src

test:
	uv run pytest -q

css:
	@echo "@import \"tailwindcss\";" > /tmp/_tw_input.css
	npx @tailwindcss/cli -i /tmp/_tw_input.css -o src/static/css/tailwind.css --content "src/templates/**/*.html"
	@rm /tmp/_tw_input.css

check: lint type test

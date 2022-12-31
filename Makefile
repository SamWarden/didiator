py := poetry run
package_dir := src

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## Install package with dependencies
	poetry install --with dev,test,lint -E di

.PHONY: lint
lint: ## Lint code with flake8, pylint, mypy
	$(py) flake8 $(package_dir)
	$(py) pylint $(package_dir)
	$(py) mypy $(package_dir)

.PHONY: test
test: ## Run tests
	$(py) pytest $(package_dir)

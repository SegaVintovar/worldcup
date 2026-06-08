PYTHON = python3
MAIN   = wc_groups.py

.PHONY: run decrypt decrypt-all

run:
	$(PYTHON) $(MAIN) predict

decrypt:
	@[ "$(id)" ] || (echo "Usage: make decrypt id=<user_id>"; exit 1)
	$(PYTHON) $(MAIN) decrypt $(id)

decrypt-all:
	$(PYTHON) $(MAIN) decrypt-all
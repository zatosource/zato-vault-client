
.PHONY: test

ENV_NAME=env
BIN_DIR=$(CURDIR)/$(ENV_NAME)/bin

default: test

# In case of any errors with virtualenv on Ubuntu 14.04 make sure you have virtualenv==12.0 installed (that exact one).

install2:
	virtualenv -p python $(CURDIR)/$(ENV_NAME)
	$(MAKE) _install

install3:
	virtualenv -p python3 $(CURDIR)/$(ENV_NAME)
	$(MAKE) _install

_install:
	$(BIN_DIR)/pip install -r $(CURDIR)/requirements.txt
	$(BIN_DIR)/python $(CURDIR)/setup.py develop
	$(BIN_DIR)/pip install -e $(CURDIR)/.

clean:
	rm -rf $(CURDIR)/$(ENV_NAME)
	rm -rf $(CURDIR)/build
	rm -rf $(CURDIR)/dist
	rm -rf $(CURDIR)/src/zato_vault_client.egg-info
	find $(CURDIR) -name '*.pyc' -exec rm {} \;

test:
	$(MAKE) clean
	$(MAKE) install2
	$(MAKE) _test
	$(MAKE) clean
	$(MAKE) install3
	$(MAKE) _test

_test:
	$(MAKE) pyflakes

pyflakes:
	$(BIN_DIR)/pyflakes $(CURDIR)/src
	$(BIN_DIR)/pyflakes $(CURDIR)/test

pypi:
	$(BIN_DIR)/python $(CURDIR)/setup.py sdist bdist_wheel
	$(BIN_DIR)/twine upload $(CURDIR)/dist/zato*
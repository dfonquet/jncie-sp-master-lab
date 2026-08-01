PROFILE ?= daily
BASELINE ?= isis
TOPOLOGY = topology/jncie-sp-$(PROFILE).clab.yml

.PHONY: help generate validate test plan up check down automation-image clean-generated

help:
	@echo "PROFILE=daily|optimized|master BASELINE=mgmt-only|isis"
	@echo "Targets: generate validate test plan up check down automation-image"

generate:
	python3 tools/build_lab.py --profile $(PROFILE) --baseline $(BASELINE)

validate: generate
	python3 tools/validate_artifacts.py --profile $(PROFILE) --baseline $(BASELINE)
	python3 tools/validate_documentation.py

test:
	python3 -m pytest -q

plan: validate
	@if docker ps --format '{{.Names}}' | grep -q '^clab-'; then echo "Refusing: another Containerlab profile is active"; exit 1; fi
	sudo containerlab apply -t $(TOPOLOGY) --dry-run

up: plan
	sudo containerlab deploy -t $(TOPOLOGY)

check:
	python3 automation/scripts/validate_runtime.py --profile $(PROFILE) --baseline $(BASELINE)

down:
	sudo containerlab destroy -t $(TOPOLOGY)

automation-image:
	docker build -t jncie-sp-automation:1.0 automation/

clean-generated:
	@echo "Generated artifacts are tracked; regenerate them instead of deleting them."

daily-plan daily-up daily-check daily-down optimized-up optimized-check optimized-down master-up master-check master-down:
	$(MAKE) PROFILE=$(word 1,$(subst -, ,$@)) $(word 2,$(subst -, ,$@))

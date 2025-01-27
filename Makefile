CONTAINER=collector-webapp\:local

docker .docker:
	docker build -t $(CONTAINER) .
	touch .docker

run:	.docker
	docker run -v $(HOME)/.keys/service-account-key.json:/app/service-account-key.json --rm $(CONTAINER)

shell:	.docker
	docker run -v $(HOME)/.keys/service-account-key.json:/app/service-account-key.json -it $(CONTAINER) /bin/bash

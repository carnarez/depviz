FLAGS=--interactive \
	            --rm \
	            --tty \
	            --user "$$(id -u)":"$$(id -g)" \
	            --volume /etc/group:/etc/group:ro \
	            --volume /etc/passwd:/etc/passwd:ro \
	            --volume /etc/shadow:/etc/shadow:ro \
	            --volume "$(PWD)/utils":/usr/src \
	            --workdir /usr/src \

build-utils:
	@docker build --tag depviz/utils utils

build-web:
	@docker build --tag depviz/web web

clean:
	-@rm -fr $$(find . -name __pycache__)

env: build-utils
	@docker run $(FLAGS) --entrypoint /bin/bash --name depviz-utils depviz/utils

serve: build-web
	@docker run $(FLAGS) --name depviz-web --publish 8000:80 depviz/web

test: build-utils
	@docker run $(FLAGS) \
	            --env COLUMNS=$(COLUMNS) \
	            --name depviz-tests \
	            depviz/utils python -m pytest --capture=no \
	                                           --color=yes \
	                                           --cov=sql_to_json \
	                                           --cov-report term-missing \
	                                           --override-ini="cache_dir=/tmp/pytest" \
	                                           --verbose \
	                                           --verbose

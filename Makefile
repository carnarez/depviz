clean:
	-@rm -fr $$(find . -name __pycache__)

env:
	@docker build --tag depviz/utils utils
	@docker run --entrypoint /bin/bash \
	            --interactive \
	            --name depviz-utils \
	            --rm \
	            --tty \
	            --user "$$(id -u)":"$$(id -g)" \
	            --volume /etc/group:/etc/group:ro \
	            --volume /etc/passwd:/etc/passwd:ro \
	            --volume /etc/shadow:/etc/shadow:ro \
	            --volume "$(PWD)/utils":/usr/src \
	            --workdir /usr/src \
	            depviz/utils

serve:
	@docker build --tag depviz/web web
	@docker run --interactive \
	            --name depviz-web \
	            --publish 8000:80 \
	            --rm \
	            --tty \
	            depviz/web

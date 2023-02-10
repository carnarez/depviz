# render markdown to html

FROM python:slim as render

ENV URL=git+https://github.com/carnarez/

WORKDIR /usr/src

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --yes git wget \
 && pip install -U pip \
 && pip install --no-cache-dir $URL/astdocs@master \
                               $URL/markdown-astdocs@master \
                               $URL/markdown-img@master \
                               $URL/markdown-insert@master \
                               $URL/markdown-script@master \
                               jinja2 \
                               lunr \
                               markdown \
                               pymdown-extensions \
                               pyyaml \
 && wget --quiet https://raw.githubusercontent.com/carnarez/markdown-render/master/build/render.py \
 && wget --quiet https://raw.githubusercontent.com/carnarez/markdown-render/master/build/template.html

COPY . .

RUN git clone --filter=blob:none --quiet https://github.com/carnarez/depviz.git \
 && mkdir utils \
 && mv depviz/utils/*.py utils \
 && rm -fr depviz \
 && ( \
      cd utils; \
      ASTDOCS_WITH_LINENOS=1 astdocs . > index.md; \
      mv *.py ..; \
    ) \
 && find . -name "*.md" | grep -e front-matter.md -e toc.md -v | while read f; do \
      mkdir -p /var/www/`dirname $f`; \
      cat front-matter.md $f > /tmp/md; \
      mv /tmp/md $f; \
    done \
 && python render.py --meta="splash=nosplash" --prefix=/var/www `find . -name "*.md" | grep -e front-matter.md -e toc.md -v`


# minify everything in place

FROM node:alpine as bundle

ENV URL=https://raw.githubusercontent.com/carnarez/markdown-render/master/style/

WORKDIR /var/www

RUN npm config set update-notifier false \
 && npm install --global --no-audit --no-fund autoprefixer clean-css-cli html-minifier postcss-cli terser | grep -v ^$ \
 && wget --quiet $URL/style.css -O _style.css \
 && wget --quiet $URL/style-highlight.css -O _style-highlight.css \
 && wget --quiet $URL/style-markdown.css -O _style-markdown.css \
 && wget --quiet $URL/style-search.css -O _style-search.css

COPY --from=render /var/www .

COPY . .

RUN rm `find . -name "*.md"` \
 && cat _style.css _style-*.css | grep -v '@import ".*"' > _bundle.css \
 && rm _style.css _style-*.css \
 && cat *.css > bundle.css_ \
 && rm *.css \
 && mv bundle.css_ style.css \
 && find . -name "*.css" | while read f; do \
      postcss $f --replace --use autoprefixer; \
      cleancss --output $f $f; \
    done \
 && find . -name "*.html" | while read f; do \
      html-minifier --collapse-boolean-attributes \
                    --collapse-whitespace \
                    --output $f \
                    --minify-css true \
                    --minify-js true \
                    --remove-attribute-quotes \
                    --remove-comments \
                    --remove-empty-attributes \
                    --remove-optional-tags \
                    --remove-redundant-attributes \
                    --remove-script-type-attributes \
                    --remove-style-link-type-attributes \
                    --use-short-doctype \
                    $f; \
    done \
 && find . -name "*.js" | while read f; do \
      terser --compress --mangle --output $f $f || echo "terser cannot minify ${f:2}, leaving as is"; \
    done


# create an entrypoint.sh to trap the httpd process

FROM busybox

RUN addgroup -S www \
 && adduser -DHS -G www -s /bin/sh www \
 && touch /etc/httpd.conf \
 && echo "/bin/httpd -c /etc/httpd.conf -f -h /var/www -p 0.0.0.0:80" > /usr/sbin/entrypoint.sh \
 && chmod +x /usr/sbin/entrypoint.sh

WORKDIR /var/www

COPY --from=bundle /var/www .

USER www

ENTRYPOINT ["/bin/sh", "-c", "/usr/sbin/entrypoint.sh"]

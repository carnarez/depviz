# render markdown to html

FROM python:slim as render

ENV URL=git+https://github.com/carnarez/

WORKDIR /usr/src

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --yes git \
 && pip install -U pip \
 && pip install --no-cache-dir $URL/astdocs@master \
                               $URL/markdown-extension-astdocs@master \
                               $URL/markdown-extension-img@master \
                               $URL/markdown-extension-insert@master \
                               $URL/markdown-extension-script@master \
                               $URL/markdown-render@master \
                               jinja2 \
                               lunr \
                               markdown \
                               pymdown-extensions \
                               pyyaml 

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
 && render-markdown --meta="splash=nosplash" --prefix=/var/www `find . -name "*.md" | grep -e front-matter.md -e toc.md -v`


# minify everything in place

FROM node:alpine as bundle

WORKDIR /var/www

COPY --from=render /var/www .

COPY . .

RUN rm `find . -name "*.md"` \
 && apk --no-cache add git \
 && npm config set update-notifier false \
 && npm install --global --no-audit --no-fund autoprefixer \
                                              clean-css-cli \
                                              html-minifier \
                                              postcss-cli \
                                              terser \
    | grep -v ^$ \
 && git clone --depth=1 https://github.com/carnarez/markdown-render-styling.git \
 && cat markdown-render-styling/style.css markdown-render-styling/style-*.css | grep -v '@import ".*"' > _bundle.css \
 && rm -fr markdown-render-styling \
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
      terser --compress --mangle --module --output $f $f; \
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

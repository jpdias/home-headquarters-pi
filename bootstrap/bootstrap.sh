#! /bin/sh -e
#set -x

apk update
apk add curl

wupiaowt() {
    # [w]ait [u]ntil [p]ort [i]s [a]ctually [o]pen [w]ith [t]imeout <who> <timeout> <target>
    if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
        echo 'Invalid parameters'
        exit 1
    fi
    if ! timeout -t $2 -s KILL /bin/sh -c "until curl -XGET -o /dev/null -sf 'http://$3'; do sleep 1s && echo '$1 waiting for $3 ...'; done"; then
        echo "$0 timeout: $3 was unreachable"
        exit 137
    fi
}

wupiaowt "$0" 70 "grafana:3000"

STATUSCODE=$(curl -i -XPOST 'http://foobar:foobar@grafana:3000/api/datasources' \
                  --write-out "%{http_code}" --output /dev/stderr \
                  --header 'Content-Type: application/json' \
                  --data-binary "{\"name\":\"influxdb\",\"type\":\"influxdb\",\"access\":\"proxy\",\"url\":\"http://influxdb:8086\",\"password\":\"foobar\",\"user\":\"foobar\",\"database\":\"telegraf\",\"basicAuth\":false,\"isDefault\":true}")

if [ $STATUSCODE -ne 200 ]; then
    echo "Unable to initialise the grafana data source"
    exit 1
fi

STATUSCODE=$(curl -i -XPOST 'http://foobar:foobar@grafana:3000/api/dashboards/db' \
                  --write-out "%{http_code}" --output /dev/stderr \
                  --header 'Content-Type: application/json' \
                  --data-binary @/system.json)

if [ $STATUSCODE -ne 200 ]; then
    echo "Unable to create the system dashboard"
    exit 1
fi

while true; do
    exec tail -s 6000000 -f /dev/null
sleep 1s
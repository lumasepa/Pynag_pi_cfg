#!/bin/bash
{% autoescape off %}

NSCA_CONF_FILE="{{NSCA_CONF_FILE}}" #"/etc/send_nsca.cfg"

DIR_PLUGINGS="{{DIR_PLUGINGS}}" #"/usr/lib/nagios/plugins"

NAGIOS_SERVER="{{NAGIOS_SERVER}}" #"193.145.118.253"

function ssend_nsca
{
	echo -e "$1\t$2\t$3\t$4" | /usr/sbin/send_nsca -H $NAGIOS_SERVER -c $NSCA_CONF_FILE
}

while (( $# )); do

	case $1 in
	{% for k,i in checks %}
	{{k}} )
	    {% for j in i %}
		{{j}}
        {% endfor %}
	;;
	{% endfor %}

	* )
		echo "$1 Parametro incorrecto"
		exit
	;;
	esac
	shift
done

{% endautoescape %}
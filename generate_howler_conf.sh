#!/bin/bash

mkdir -p /etc/howler/conf

HOWLER_CLASSIFICATION_PATH="/etc/howler/conf/classification.yml"
HOWLER_CONF_PATH="/etc/howler/conf/config.yml"

HOWLER_CLASSIFICATION_DATA="enforce: false
dynamic_groups: false"

function create_classification() {
  echo "Creating $HOWLER_CLASSIFICATION_PATH"
  cat <<<$HOWLER_CLASSIFICATION_DATA >$HOWLER_CLASSIFICATION_PATH
}

function create_config() {
  HOWLER_CONF_DATA="auth:
  internal:
    enabled: true

datastore:
  ilm:
    enabled: false
    indexes: {}

logging:
  log_level: INFO
  log_as_json: false

system:
  type: development

ui:
  audit: true
  debug: false
  enforce_quota: false
  validate_session_useragent: false
  static_folder: /etc/howler/static
"

  echo "Creating $HOWLER_CONF_PATH"
  cat <<<$HOWLER_CONF_DATA >$HOWLER_CONF_PATH
}

write=true
if [[ -f "$HOWLER_CLASSIFICATION_PATH" ]]; then
  while [ true ]; do
    read -n 1 -p "$HOWLER_CLASSIFICATION_PATH already exists. Overwrite? (y/N) " res
    if [ -z "$res" ]; then
      res="n"
    else
      echo
    fi

    case "$res" in
    [yY])
      break
      ;;
    [nN])
      write=false
      break
      ;;
    *)
      echo "Enter a valid response.\n"
      ;;
    esac
  done
fi

if [ "$write" = true ]; then
  create_classification
fi

write=true
if [[ -f "$HOWLER_CONF_PATH" ]]; then
  while [ true ]; do
    read -n 1 -p "$HOWLER_CONF_PATH already exists. Overwrite? (y/N) " res
    if [ -z "$res" ]; then
      res="n"
    else
      echo
    fi

    case "$res" in
    [yY])
      break
      ;;
    [nN])
      write=false
      break
      ;;
    *)
      echo "Enter a valid response.\n"
      ;;
    esac
  done
fi

if [ "$write" = true ]; then
  create_config
fi

echo "Creating lookups..."
mkdir -p /etc/howler/lookups
python howler/external/generate_mitre.py /etc/howler/lookups
echo "Completed configuration!"

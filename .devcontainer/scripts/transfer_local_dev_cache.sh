#!/bin/bash

if [ ! -d "../../.local_dev_data" ]; then
    mkdir ../../.local_dev_data
fi

cp -r /local_dev_data ../../.local_dev_data
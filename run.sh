#!/bin/bash

while true
do
    poetry run python agents_of_inference/main.py
    if [ $? -ne 0 ]; then
        echo "Script failed. Restarting..."
    else
        echo "Script completed successfully."
    fi
done

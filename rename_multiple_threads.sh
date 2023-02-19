#!/bin/bash

# Get the prefix and postfix arguments
PREFIX="$1"
CENTER="$2"
POSTFIX="$3"

# postfix should include the t, but not the number. ex. sim_name_t, but not sim_name_t12
# Loop through all directories that match the pattern "${PREFIX}*"
for DIR in ${PREFIX}${CENTER}${POSTFIX}*
do
    # Rename the directory to the new name
    NEW_NAME="${PREFIX}${POSTFIX}"
    mv "${DIR}" "${NEW_NAME}"
done

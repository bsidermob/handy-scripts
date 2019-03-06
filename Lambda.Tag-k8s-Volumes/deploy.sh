#!/bin/bash
set -x

# variables
tmp=$(mktemp)
function_name="ec2-tag-k8s-volumes"
list_of_environments="default"

# Rename function and deploy to multiple accounts
for environment in $list_of_environments
do
	echo "working on $environment"
	lowercase_environment=$(echo $environment | tr '[:upper:]' '[:lower:]')
	export AWS_PROFILE=$environment
	jq '.function = "'${lowercase_environment}-${function_name}'"' metadata.json > "$tmp" && mv "$tmp" metadata.json
	cp ${function_name}.py ${lowercase_environment}-${function_name}.py
	lambkin publish --role "lambda_basic_execution"
	rm ${lowercase_environment}-${function_name}.py
	lambkin schedule --cron '0 * * * ? *'
done

